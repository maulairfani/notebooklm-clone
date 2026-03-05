import uuid

# TODO(bug): `create_agent` tidak ada di LangChain — ganti ke `create_tool_calling_agent`
# dari `langchain.agents`, dan sesuaikan cara invoke-nya (pakai AgentExecutor atau LCEL chain)
from langchain.agents import create_agent
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import BaseTool
from langchain_groq import ChatGroq
from langchain_postgres import PGVector
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.exceptions import NotFoundError, UnprocessableError
from app.models.chat import Chat, Message
from app.models.notebook import Notebook
from app.models.source import Source
from app.services.embedding_service import get_embeddings


class SearchSourcesTool(BaseTool):
    name: str = "search_sources"
    description: str = (
        "Search through the uploaded documents for relevant information. "
        "Use this to answer questions based on the user's sources."
    )
    # TODO(minor): mutable default list bisa menyebabkan state bleeding antar instance Pydantic.
    # Ganti ke `stores: list[PGVector] = Field(default_factory=list)`
    stores: list[PGVector] = []

    def _run(
        self,
        query: str,
        run_manager: CallbackManagerForToolRun | None = None,
    ) -> str:
        all_docs = []
        for vs in self.stores:
            docs = vs.similarity_search(query, k=3)
            all_docs.extend(docs)
        if not all_docs:
            return "No relevant information found in the sources."
        return "\n\n---\n\n".join(doc.page_content for doc in all_docs)


class ChatService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_chat(
        self,
        notebook_id: uuid.UUID,
        user_id: uuid.UUID,
        title: str | None = None,
    ) -> Chat:
        await self._get_notebook(notebook_id, user_id)
        chat = Chat(notebook_id=notebook_id, title=title)
        self.db.add(chat)
        await self.db.flush()
        await self.db.refresh(chat)
        return chat

    async def get_chats(
        self, notebook_id: uuid.UUID, user_id: uuid.UUID
    ) -> list[Chat]:
        await self._get_notebook(notebook_id, user_id)
        result = await self.db.execute(
            select(Chat)
            .where(Chat.notebook_id == notebook_id)
            .order_by(Chat.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_chat(
        self,
        chat_id: uuid.UUID,
        notebook_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Chat:
        await self._get_notebook(notebook_id, user_id)
        result = await self.db.execute(
            select(Chat)
            .options(selectinload(Chat.messages))
            .where(Chat.id == chat_id, Chat.notebook_id == notebook_id)
        )
        chat = result.scalar_one_or_none()
        if chat is None:
            raise NotFoundError("Chat not found")
        return chat

    async def delete_chat(
        self,
        chat_id: uuid.UUID,
        notebook_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        chat = await self.get_chat(chat_id, notebook_id, user_id)
        await self.db.delete(chat)
        await self.db.flush()

    async def send_message(
        self,
        chat_id: uuid.UUID,
        notebook_id: uuid.UUID,
        user_id: uuid.UUID,
        content: str,
    ) -> Message:
        chat = await self.get_chat(chat_id, notebook_id, user_id)

        # Get ready sources for this notebook
        result = await self.db.execute(
            select(Source).where(
                Source.notebook_id == notebook_id, Source.status == "ready"
            )
        )
        sources = list(result.scalars().all())
        if not sources:
            raise UnprocessableError(
                "No processed sources available. Upload and process sources first."
            )

        # Save user message
        user_message = Message(chat_id=chat_id, role="user", content=content)
        self.db.add(user_message)
        await self.db.flush()

        # Build chat history for context
        history: list[HumanMessage | AIMessage] = []
        for msg in chat.messages:
            if msg.role == "user":
                history.append(HumanMessage(content=msg.content))
            else:
                history.append(AIMessage(content=msg.content))

        # TODO(perf): `_run_agent` adalah blocking call (embedding + LLM inference) yang di-invoke
        # langsung dari async context — ini nge-block seluruh event loop.
        # Ganti ke: `response_text = await asyncio.to_thread(self._run_agent, sources, history, content)`
        # Run RAG agent
        response_text = self._run_agent(sources, history, content)

        # Save assistant message
        assistant_message = Message(
            chat_id=chat_id, role="assistant", content=response_text
        )
        self.db.add(assistant_message)
        await self.db.flush()
        await self.db.refresh(assistant_message)
        return assistant_message

    def _run_agent(
        self,
        sources: list[Source],
        history: list[HumanMessage | AIMessage],
        query: str,
    ) -> str:
        embeddings = get_embeddings()

        # TODO(perf): PGVector store di-instantiate ulang tiap pesan — pertimbangkan caching
        # per collection_name agar tidak buat koneksi baru setiap request.
        # Build vector stores for all source collections
        stores = []
        for source in sources:
            store = PGVector(
                embeddings=embeddings,
                collection_name=f"source_{source.id}",
                connection=settings.SYNC_DATABASE_URL,
            )
            stores.append(store)

        search_tool = SearchSourcesTool(stores=stores)

        # TODO(perf): ChatGroq di-instantiate ulang tiap pesan — jadikan singleton/module-level instance.
        # Init LLM
        llm = ChatGroq(
            api_key=settings.GROQ_API_KEY,
            model=settings.GROQ_MODEL,
            temperature=0,
        )

        # Create agent using langchain's create_agent
        agent = create_agent(
            llm,
            tools=[search_tool],
            prompt=(
                "You are a helpful research assistant. Answer questions based on the provided sources. "
                "Always use the search_sources tool to find relevant information before answering. "
                "If the sources don't contain relevant information, say so clearly. "
                "Cite information from the sources when possible."
            ),
        )

        # Build messages and invoke
        messages = history + [HumanMessage(content=query)]
        result = agent.invoke({"messages": messages})

        # Extract the final AI message
        ai_messages = [
            m for m in result["messages"] if isinstance(m, AIMessage) and m.content
        ]
        if ai_messages:
            return ai_messages[-1].content
        return "I couldn't generate a response. Please try again."

    async def _get_notebook(
        self, notebook_id: uuid.UUID, user_id: uuid.UUID
    ) -> Notebook:
        result = await self.db.execute(
            select(Notebook).where(
                Notebook.id == notebook_id, Notebook.user_id == user_id
            )
        )
        notebook = result.scalar_one_or_none()
        if notebook is None:
            raise NotFoundError("Notebook not found")
        return notebook

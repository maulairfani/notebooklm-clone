import io
from unittest.mock import MagicMock, patch

import pytest
from httpx import AsyncClient


async def _register_and_login(client: AsyncClient, email: str, password: str = "securepass") -> str:
    reg = await client.post(
        "/api/v1/auth/register", json={"email": email, "password": password}
    )
    return reg.json()["data"]["access_token"]


async def _create_notebook(client: AsyncClient, token: str, title: str = "My Notebook") -> str:
    resp = await client.post(
        "/api/v1/notebooks",
        json={"title": title},
        headers={"Authorization": f"Bearer {token}"},
    )
    return resp.json()["data"]["id"]


def _pdf_file(name: str = "test.pdf") -> tuple[str, tuple[str, bytes, str]]:
    content = b"%PDF-1.4 fake pdf content"
    return ("file", (name, io.BytesIO(content), "application/pdf"))


@pytest.mark.asyncio
async def test_upload_pdf_success(client: AsyncClient) -> None:
    token = await _register_and_login(client, "src1@example.com")
    notebook_id = await _create_notebook(client, token)

    with (
        patch("app.api.v1.endpoints.sources.process_source") as mock_task,
        patch("app.api.v1.endpoints.sources.os.makedirs"),
        patch("builtins.open", MagicMock()),
    ):
        mock_task.delay = MagicMock()
        response = await client.post(
            f"/api/v1/notebooks/{notebook_id}/sources",
            files=[_pdf_file()],
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 202
    body = response.json()
    assert body["status_code"] == 202
    assert body["data"]["status"] == "pending"
    assert body["data"]["source_type"] == "pdf"
    assert body["data"]["notebook_id"] == notebook_id
    assert mock_task.delay.call_count == 1


@pytest.mark.asyncio
async def test_upload_pdf_unauthenticated(client: AsyncClient) -> None:
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.post(
        f"/api/v1/notebooks/{fake_id}/sources",
        files=[_pdf_file()],
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_upload_pdf_wrong_notebook(client: AsyncClient) -> None:
    token = await _register_and_login(client, "src2@example.com")
    fake_id = "00000000-0000-0000-0000-000000000000"

    with (
        patch("app.api.v1.endpoints.sources.process_source"),
        patch("app.api.v1.endpoints.sources.os.makedirs"),
        patch("builtins.open", MagicMock()),
    ):
        response = await client.post(
            f"/api/v1/notebooks/{fake_id}/sources",
            files=[_pdf_file()],
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_upload_non_pdf(client: AsyncClient) -> None:
    token = await _register_and_login(client, "src3@example.com")
    notebook_id = await _create_notebook(client, token)

    response = await client.post(
        f"/api/v1/notebooks/{notebook_id}/sources",
        files=[("file", ("test.txt", io.BytesIO(b"hello"), "text/plain"))],
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_sources_empty(client: AsyncClient) -> None:
    token = await _register_and_login(client, "src4@example.com")
    notebook_id = await _create_notebook(client, token)

    response = await client.get(
        f"/api/v1/notebooks/{notebook_id}/sources",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status_code"] == 200
    assert body["data"] == []


@pytest.mark.asyncio
async def test_list_sources(client: AsyncClient) -> None:
    token = await _register_and_login(client, "src5@example.com")
    notebook_id = await _create_notebook(client, token)

    with (
        patch("app.api.v1.endpoints.sources.process_source") as mock_task,
        patch("app.api.v1.endpoints.sources.os.makedirs"),
        patch("builtins.open", MagicMock()),
    ):
        mock_task.delay = MagicMock()
        await client.post(
            f"/api/v1/notebooks/{notebook_id}/sources",
            files=[_pdf_file("a.pdf")],
            headers={"Authorization": f"Bearer {token}"},
        )
        await client.post(
            f"/api/v1/notebooks/{notebook_id}/sources",
            files=[_pdf_file("b.pdf")],
            headers={"Authorization": f"Bearer {token}"},
        )

    response = await client.get(
        f"/api/v1/notebooks/{notebook_id}/sources",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert len(response.json()["data"]) == 2


@pytest.mark.asyncio
async def test_get_source_success(client: AsyncClient) -> None:
    token = await _register_and_login(client, "src6@example.com")
    notebook_id = await _create_notebook(client, token)

    with (
        patch("app.api.v1.endpoints.sources.process_source") as mock_task,
        patch("app.api.v1.endpoints.sources.os.makedirs"),
        patch("builtins.open", MagicMock()),
    ):
        mock_task.delay = MagicMock()
        upload_resp = await client.post(
            f"/api/v1/notebooks/{notebook_id}/sources",
            files=[_pdf_file()],
            headers={"Authorization": f"Bearer {token}"},
        )

    source_id = upload_resp.json()["data"]["id"]
    response = await client.get(
        f"/api/v1/notebooks/{notebook_id}/sources/{source_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["id"] == source_id


@pytest.mark.asyncio
async def test_get_source_not_found(client: AsyncClient) -> None:
    token = await _register_and_login(client, "src7@example.com")
    notebook_id = await _create_notebook(client, token)
    fake_id = "00000000-0000-0000-0000-000000000000"

    response = await client.get(
        f"/api/v1/notebooks/{notebook_id}/sources/{fake_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_source_other_user(client: AsyncClient) -> None:
    token_a = await _register_and_login(client, "srca@example.com")
    token_b = await _register_and_login(client, "srcb@example.com")
    notebook_id = await _create_notebook(client, token_a)

    with (
        patch("app.api.v1.endpoints.sources.process_source") as mock_task,
        patch("app.api.v1.endpoints.sources.os.makedirs"),
        patch("builtins.open", MagicMock()),
    ):
        mock_task.delay = MagicMock()
        upload_resp = await client.post(
            f"/api/v1/notebooks/{notebook_id}/sources",
            files=[_pdf_file()],
            headers={"Authorization": f"Bearer {token_a}"},
        )

    source_id = upload_resp.json()["data"]["id"]
    response = await client.get(
        f"/api/v1/notebooks/{notebook_id}/sources/{source_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_source_success(client: AsyncClient) -> None:
    token = await _register_and_login(client, "src8@example.com")
    notebook_id = await _create_notebook(client, token)

    with (
        patch("app.api.v1.endpoints.sources.process_source") as mock_task,
        patch("app.api.v1.endpoints.sources.os.makedirs"),
        patch("builtins.open", MagicMock()),
    ):
        mock_task.delay = MagicMock()
        upload_resp = await client.post(
            f"/api/v1/notebooks/{notebook_id}/sources",
            files=[_pdf_file()],
            headers={"Authorization": f"Bearer {token}"},
        )

    source_id = upload_resp.json()["data"]["id"]

    with patch("app.services.source_service.os.path.exists", return_value=False):
        response = await client.delete(
            f"/api/v1/notebooks/{notebook_id}/sources/{source_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200

    get_resp = await client.get(
        f"/api/v1/notebooks/{notebook_id}/sources/{source_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_source_not_found(client: AsyncClient) -> None:
    token = await _register_and_login(client, "src9@example.com")
    notebook_id = await _create_notebook(client, token)
    fake_id = "00000000-0000-0000-0000-000000000000"

    response = await client.delete(
        f"/api/v1/notebooks/{notebook_id}/sources/{fake_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404

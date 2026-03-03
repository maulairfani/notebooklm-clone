import pytest
from httpx import AsyncClient


async def _register_and_login(client: AsyncClient, email: str, password: str = "securepass") -> str:
    reg = await client.post(
        "/api/v1/auth/register", json={"email": email, "password": password}
    )
    return reg.json()["data"]["access_token"]


@pytest.mark.asyncio
async def test_create_notebook_success(client: AsyncClient) -> None:
    token = await _register_and_login(client, "nb1@example.com")
    response = await client.post(
        "/api/v1/notebooks",
        json={"title": "My Notebook"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status_code"] == 201
    assert body["data"]["title"] == "My Notebook"
    assert "id" in body["data"]
    assert "user_id" in body["data"]


@pytest.mark.asyncio
async def test_create_notebook_unauthenticated(client: AsyncClient) -> None:
    response = await client.post("/api/v1/notebooks", json={"title": "My Notebook"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_notebooks_empty(client: AsyncClient) -> None:
    token = await _register_and_login(client, "nb2@example.com")
    response = await client.get(
        "/api/v1/notebooks",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status_code"] == 200
    assert body["data"] == []


@pytest.mark.asyncio
async def test_list_notebooks(client: AsyncClient) -> None:
    token = await _register_and_login(client, "nb3@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    await client.post("/api/v1/notebooks", json={"title": "First"}, headers=headers)
    await client.post("/api/v1/notebooks", json={"title": "Second"}, headers=headers)

    response = await client.get("/api/v1/notebooks", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert len(body["data"]) == 2


@pytest.mark.asyncio
async def test_get_notebook_success(client: AsyncClient) -> None:
    token = await _register_and_login(client, "nb4@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    create_resp = await client.post(
        "/api/v1/notebooks", json={"title": "Get Me"}, headers=headers
    )
    notebook_id = create_resp.json()["data"]["id"]

    response = await client.get(f"/api/v1/notebooks/{notebook_id}", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["id"] == notebook_id
    assert body["data"]["title"] == "Get Me"


@pytest.mark.asyncio
async def test_get_notebook_not_found(client: AsyncClient) -> None:
    token = await _register_and_login(client, "nb5@example.com")
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.get(
        f"/api/v1/notebooks/{fake_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_notebook_other_user(client: AsyncClient) -> None:
    token_a = await _register_and_login(client, "nba@example.com")
    token_b = await _register_and_login(client, "nbb@example.com")

    create_resp = await client.post(
        "/api/v1/notebooks",
        json={"title": "User A Notebook"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    notebook_id = create_resp.json()["data"]["id"]

    response = await client.get(
        f"/api/v1/notebooks/{notebook_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_notebook_success(client: AsyncClient) -> None:
    token = await _register_and_login(client, "nb6@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    create_resp = await client.post(
        "/api/v1/notebooks", json={"title": "Old Title"}, headers=headers
    )
    notebook_id = create_resp.json()["data"]["id"]

    response = await client.put(
        f"/api/v1/notebooks/{notebook_id}",
        json={"title": "New Title"},
        headers=headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["title"] == "New Title"


@pytest.mark.asyncio
async def test_update_notebook_not_found(client: AsyncClient) -> None:
    token = await _register_and_login(client, "nb7@example.com")
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.put(
        f"/api/v1/notebooks/{fake_id}",
        json={"title": "New Title"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_notebook_success(client: AsyncClient) -> None:
    token = await _register_and_login(client, "nb8@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    create_resp = await client.post(
        "/api/v1/notebooks", json={"title": "Delete Me"}, headers=headers
    )
    notebook_id = create_resp.json()["data"]["id"]

    response = await client.delete(f"/api/v1/notebooks/{notebook_id}", headers=headers)
    assert response.status_code == 200

    get_resp = await client.get(f"/api/v1/notebooks/{notebook_id}", headers=headers)
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_notebook_not_found(client: AsyncClient) -> None:
    token = await _register_and_login(client, "nb9@example.com")
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.delete(
        f"/api/v1/notebooks/{fake_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404

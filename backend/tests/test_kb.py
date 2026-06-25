"""Tests for knowledge base upload, list, detail, delete, and retry."""

import io

import pytest
from httpx import ASGITransport, AsyncClient
from src.main import app


@pytest.fixture
async def test_client():
    """Create test client using shared test database from conftest."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest.fixture
async def auth_token(test_client, test_session_factory):
    """Get authentication token for test user."""
    from src.core.security import hash_password
    from src.db.models import User

    async with test_session_factory() as session:
        session.add(
            User(
                username="testuser",
                password_hash=hash_password("testpass"),
            )
        )
        await session.commit()

    response = await test_client.post(
        "/api/auth/login",
        json={"username": "testuser", "password": "testpass"},
    )
    assert response.status_code == 200
    data = response.json()
    return data["data"]["access_token"]


@pytest.mark.asyncio
async def test_upload_file_success(test_client, auth_token):
    """测试上传 .md 文件成功."""
    file_content = b"# Test Markdown\n\nThis is a test file."
    files = {"file": ("test.md", io.BytesIO(file_content), "text/markdown")}

    response = await test_client.post(
        "/api/kb/upload",
        files=files,
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert data["data"]["filename"] == "test.md"
    assert data["data"]["status"] == "processing"


@pytest.mark.asyncio
async def test_upload_file_invalid_format(test_client, auth_token):
    """测试上传非 .md 文件返回 400."""
    file_content = b"Not a markdown file"
    files = {"file": ("test.txt", io.BytesIO(file_content), "text/plain")}

    response = await test_client.post(
        "/api/kb/upload",
        files=files,
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 400
    data = response.json()
    assert data["detail"]["code"] == 4001
    assert "仅支持 .md 格式文件" in data["detail"]["message"]


@pytest.mark.asyncio
async def test_list_files(test_client, auth_token):
    """测试获取文件列表."""
    # 先上传一个文件
    file_content = b"# Test File\n\nContent here."
    files = {"file": ("list_test.md", io.BytesIO(file_content), "text/markdown")}

    await test_client.post(
        "/api/kb/upload",
        files=files,
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    # 获取列表
    response = await test_client.get(
        "/api/kb/files",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert "items" in data["data"]
    assert data["data"]["total"] >= 1


@pytest.mark.asyncio
async def test_get_file_detail(test_client, auth_token):
    """测试获取文件详情."""
    # 先上传一个文件
    file_content = b"# Detail Test\n\nDetail content."
    files = {"file": ("detail_test.md", io.BytesIO(file_content), "text/markdown")}

    upload_response = await test_client.post(
        "/api/kb/upload",
        files=files,
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    file_id = upload_response.json()["data"]["id"]

    # 获取详情
    response = await test_client.get(
        f"/api/kb/files/{file_id}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert data["data"]["id"] == file_id
    assert data["data"]["filename"] == "detail_test.md"


@pytest.mark.asyncio
async def test_get_file_not_found(test_client, auth_token):
    """测试获取不存在的文件返回 404."""
    response = await test_client.get(
        "/api/kb/files/99999",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 404
    data = response.json()
    assert data["detail"]["code"] == 404
    assert "文件不存在" in data["detail"]["message"]


@pytest.mark.asyncio
async def test_delete_file(test_client, auth_token):
    """测试删除文件."""
    # 先上传一个文件
    file_content = b"# Delete Test\n\nTo be deleted."
    files = {"file": ("delete_test.md", io.BytesIO(file_content), "text/markdown")}

    upload_response = await test_client.post(
        "/api/kb/upload",
        files=files,
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    file_id = upload_response.json()["data"]["id"]

    # 删除文件
    response = await test_client.delete(
        f"/api/kb/files/{file_id}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200

    # 验证文件已删除
    get_response = await test_client.get(
        f"/api/kb/files/{file_id}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert get_response.status_code == 404

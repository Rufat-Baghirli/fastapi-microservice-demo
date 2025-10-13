import pytest
from httpx import AsyncClient
from fastapi import status

pytestmark = pytest.mark.asyncio


async def test_health_check(client: AsyncClient):
    """
    Tests the /health endpoint to ensure the application is running
    and can connect to its dependencies.
    """
    response = await client.get("/health")

    assert response.status_code == status.HTTP_200_OK

    json_response = response.json()
    assert "status" in json_response
    assert json_response["status"] in ["healthy", "degraded"]
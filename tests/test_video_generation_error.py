import pytest
from aioresponses import aioresponses
from bot.openrouter_client import OpenRouterClient, VideoGenerationError


@pytest.fixture
def client():
    return OpenRouterClient("test_api_key")


@pytest.mark.asyncio
async def test_generate_video_ip_infringement(client):
    with aioresponses() as mocked:
        mocked.post(
            "https://openrouter.ai/api/v1/videos",
            payload={
                "id": "job-123",
                "polling_url": "https://openrouter.ai/api/v1/videos/job-123",
                "status": "pending",
            },
        )
        mocked.get(
            "https://openrouter.ai/api/v1/videos/job-123",
            payload={
                "id": "job-123",
                "status": "failed",
                "error": "Output data is suspected of being involved in IP infringement",
            },
        )
        with pytest.raises(VideoGenerationError) as exc_info:
            await client.generate_video("real person name", user_id=1)
        assert exc_info.value.is_ip_infringement is True

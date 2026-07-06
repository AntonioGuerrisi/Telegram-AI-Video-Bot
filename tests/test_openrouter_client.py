import pytest
from aioresponses import CallbackResult, aioresponses
from bot.openrouter_client import OpenRouterClient, VideoGenerationError


@pytest.fixture
def client():
    return OpenRouterClient("test_api_key")


@pytest.mark.asyncio
async def test_generate_video_text_only(client):
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
                "status": "completed",
                "unsigned_urls": ["https://example.com/video.mp4"],
            },
        )
        url = await client.generate_video("a cat dancing", user_id=1)
        assert url == "https://example.com/video.mp4"


@pytest.mark.asyncio
async def test_generate_video_payload_includes_defaults(client):
        captured_payload = {}

        def callback(url, **kwargs):
            captured_payload.update(kwargs.get("json", {}))
            return CallbackResult(
                payload={
                    "id": "job-123",
                    "polling_url": "https://openrouter.ai/api/v1/videos/job-123",
                    "status": "pending",
                }
            )

        def poll_callback(url, **kwargs):
            return CallbackResult(
                payload={
                    "id": "job-123",
                    "status": "completed",
                    "unsigned_urls": ["https://example.com/video.mp4"],
                }
            )

        with aioresponses() as mocked:
            mocked.post(
                "https://openrouter.ai/api/v1/videos",
                callback=callback,
            )
            mocked.get(
                "https://openrouter.ai/api/v1/videos/job-123",
                callback=poll_callback,
            )
            url = await client.generate_video("a cat dancing", user_id=1, image_data=b"image-bytes")
            assert url == "https://example.com/video.mp4"
            assert captured_payload["aspect_ratio"] == "9:16"
            assert captured_payload["resolution"] == "720p"
            assert captured_payload["duration"] == 10
            assert "frame_images" in captured_payload
            assert captured_payload["frame_images"][0]["frame_type"] == "first_frame"


@pytest.mark.asyncio
async def test_generate_video_failed_status_raises(client):
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
                "error": "generation failed",
            },
        )
        with pytest.raises(VideoGenerationError) as exc_info:
            await client.generate_video("a cat dancing", user_id=1)
        assert exc_info.value.is_ip_infringement is False
        assert "generation failed" in str(exc_info.value).lower()

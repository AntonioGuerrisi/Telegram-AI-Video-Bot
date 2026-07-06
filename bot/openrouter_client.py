import asyncio
import base64
import logging
from typing import Optional

import aiofiles
import aiohttp


logger = logging.getLogger("tg_video_bot")


class VideoGenerationError(Exception):
    """Raised when OpenRouter video generation fails with a meaningful reason."""

    def __init__(self, message: str, reason: str = ""):
        super().__init__(message)
        self.reason = reason
        self.is_ip_infringement = "ip infringement" in reason.lower() or "нарушение" in reason.lower()


class OpenRouterClient:
    BASE_URL = "https://openrouter.ai/api/v1"
    MODEL = "alibaba/happyhorse-1.1"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    async def generate_video(
        self, prompt: str, user_id: int, image_data: Optional[bytes] = None
    ) -> str:
        payload = {
            "model": self.MODEL,
            "prompt": prompt,
            "aspect_ratio": "9:16",
            "resolution": "720p",
            "duration": 10,
        }
        if image_data:
            b64 = base64.b64encode(image_data).decode("utf-8")
            payload["frame_images"] = [
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
                    "frame_type": "first_frame",
                }
            ]

        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.post(
                f"{self.BASE_URL}/videos",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=120),
            ) as response:
                response.raise_for_status()
                data = await response.json()

            job_id = data.get("id")
            polling_url = data.get("polling_url")
            if not job_id or not polling_url:
                raise RuntimeError(f"OpenRouter did not return polling info: {data}")

            logger.info("Video job submitted for user %s: %s", user_id, job_id)
            video_url = await self._poll_video(session, polling_url, user_id, job_id)
            logger.info("Video generated for user %s: %s", user_id, video_url)
            return video_url

    async def _poll_video(
        self,
        session: aiohttp.ClientSession,
        polling_url: str,
        user_id: int,
        job_id: str,
        max_attempts: int = 120,
        sleep_seconds: float = 5.0,
    ) -> str:
        for attempt in range(max_attempts):
            async with session.get(
                polling_url,
                headers=self.headers,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as response:
                response.raise_for_status()
                status_data = await response.json()

            status = status_data.get("status")
            logger.info(
                "Job %s status for user %s: %s (attempt %s/%s)",
                job_id,
                user_id,
                status,
                attempt + 1,
                max_attempts,
            )

            if status == "completed":
                urls = status_data.get("unsigned_urls", [])
                if not urls:
                    raise RuntimeError(f"Job completed but no video URLs: {status_data}")
                return urls[0]

            if status == "failed":
                error = status_data.get("error", "Unknown error")
                raise VideoGenerationError(
                    f"Video generation failed: {error}",
                    reason=error,
                )

            await asyncio.sleep(sleep_seconds)

        raise VideoGenerationError(
            f"Video generation timed out after {max_attempts} attempts",
            reason="timeout",
        )

    async def download_video(self, url: str, output_path: str) -> str:
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=300)) as response:
                response.raise_for_status()
                async with aiofiles.open(output_path, "wb") as f:
                    async for chunk in response.content.iter_chunked(8192):
                        await f.write(chunk)
        return output_path

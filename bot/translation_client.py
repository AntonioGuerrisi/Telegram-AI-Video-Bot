import aiohttp
import logging


logger = logging.getLogger("tg_video_bot")


class TranslationClient:
    BASE_URL = "https://openrouter.ai/api/v1"
    MODEL = "qwen/qwen3.7-plus"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    async def translate_to_russian(self, text: str) -> str:
        payload = {
            "model": self.MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a translator. Translate the following English video generation prompt "
                        "into natural Russian. Preserve structure and meaning. Output only the translation, "
                        "no explanations."
                    ),
                },
                {"role": "user", "content": text},
            ],
            "temperature": 0.3,
        }

        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.post(
                f"{self.BASE_URL}/chat/completions",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=60),
            ) as response:
                response.raise_for_status()
                data = await response.json()

        choices = data.get("choices", [])
        if not choices:
            raise RuntimeError("OpenRouter returned no choices")

        return choices[0]["message"].get("content", text).strip()

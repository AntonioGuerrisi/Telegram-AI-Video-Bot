import base64
import json
import logging
from typing import Optional

import aiohttp


logger = logging.getLogger("tg_video_bot")


class PromptEngineerClient:
    BASE_URL = "https://openrouter.ai/api/v1"
    MODEL = "qwen/qwen3.7-plus"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    async def enhance_prompt(
        self,
        user_prompt: str,
        system_prompt: str,
        chat_history: Optional[list[dict]] = None,
        image_data: Optional[bytes] = None,
    ) -> dict:
        messages = [{"role": "system", "content": system_prompt}]
        if chat_history:
            messages.extend(chat_history)

        if image_data:
            b64 = base64.b64encode(image_data).decode("utf-8")
            messages.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
                    },
                ],
            })
        else:
            messages.append({"role": "user", "content": user_prompt})

        payload = {
            "model": self.MODEL,
            "messages": messages,
            "temperature": 0.7,
        }

        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.post(
                f"{self.BASE_URL}/chat/completions",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=120),
            ) as response:
                response.raise_for_status()
                data = await response.json()

        choices = data.get("choices", [])
        if not choices:
            raise RuntimeError("OpenRouter returned no choices")

        message = choices[0].get("message", {})
        content = message.get("content", "")
        return {"content": content, "role": "assistant"}

    @staticmethod
    def extract_code_block(content: str) -> Optional[str]:
        if "```" not in content:
            return None
        parts = content.split("```")
        if len(parts) >= 3:
            code = parts[1]
            if code.startswith(("prompt\n", "Prompt\n", "video\n", "Video\n")):
                code = code.split("\n", 1)[1]
            return code.strip()
        return None

    @staticmethod
    def is_clarification(content: str) -> bool:
        lowered = content.lower()
        has_question = "?" in content
        has_code = "```" in content
        if has_code:
            return False
        return has_question or any(
            marker in lowered
            for marker in [
                "could you",
                "can you",
                "please tell",
                "specify",
                "clarify",
                "what",
                "which",
                "how",
                "would you",
            ]
        )

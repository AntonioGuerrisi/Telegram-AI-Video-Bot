import pytest
from aioresponses import aioresponses
from bot.translation_client import TranslationClient


@pytest.fixture
def client():
    return TranslationClient("test_api_key")


@pytest.mark.asyncio
async def test_translate_to_russian(client):
    with aioresponses() as mocked:
        mocked.post(
            "https://openrouter.ai/api/v1/chat/completions",
            payload={
                "choices": [
                    {"message": {"content": "Кот танцует под дождем"}}
                ]
            },
        )
        result = await client.translate_to_russian("A cat dancing in the rain")
        assert result == "Кот танцует под дождем"

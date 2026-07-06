import os
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    bot_token: str
    openrouter_api_key: str
    openrouter_prompt_key: str
    log_level: str = "INFO"


def load_settings(env_path: str | None = None) -> Settings:
    if env_path is not None:
        load_dotenv(env_path)
    else:
        load_dotenv()
    bot_token = os.getenv("BOT_TOKEN")
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
    openrouter_prompt_key = os.getenv("OPENROUTER_PROMPT_KEY", openrouter_api_key)
    log_level = os.getenv("LOG_LEVEL", "INFO")

    if not bot_token:
        raise ValueError("BOT_TOKEN environment variable is required")
    if not openrouter_api_key:
        raise ValueError("OPENROUTER_API_KEY environment variable is required")
    if not openrouter_prompt_key:
        raise ValueError("OPENROUTER_PROMPT_KEY environment variable is required")

    return Settings(
        bot_token=bot_token,
        openrouter_api_key=openrouter_api_key,
        openrouter_prompt_key=openrouter_prompt_key,
        log_level=log_level,
    )

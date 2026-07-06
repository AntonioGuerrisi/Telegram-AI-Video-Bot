# Telegram Video Bot — Design Spec

## Goal
Build an async Telegram bot that generates short videos from user text prompts or uploaded images using the OpenRouter HappyHorse 1.1 video generation API.

## Requirements

### Functional
- Command `/start` sends a welcome/instruction message in Russian.
- Command `/video <prompt>` starts text-to-video generation.
- A plain text message (not a command) is treated as a video prompt.
- An uploaded image with an optional caption is treated as image-to-video generation; the caption is the prompt.
- Default generation parameters: aspect ratio 9:16, resolution 720p, duration 10 seconds.
- Bot immediately replies with a "generation in progress" message.
- Background async task polls OpenRouter until the video is ready, then downloads and sends it to the user.
- Final video is sent as a Telegram video note or regular video file.

### Non-functional
- No database; all logs are written to text files.
- Per-user log files plus a combined application log.
- Comprehensive error handling with user-friendly Russian messages; no stack traces or raw errors sent to Telegram.
- No user rate limits or access control; open to all users.
- Runnable locally in PyCharm with a `.env` file.
- Docker-ready for later server deployment.

## Architecture
- `aiogram` 3.x polling dispatcher.
- `aiohttp` async HTTP client for OpenRouter.
- In-memory background tasks for generation/polling.
- File-based logging via Python stdlib `logging` with rotating handlers.

## Modules
- `bot/config.py` — environment configuration and validation.
- `bot/logger.py` — file loggers per user and app-wide logger.
- `bot/openrouter_client.py` — async OpenRouter video generation, polling, download.
- `bot/handlers.py` — Telegram command/message handlers.
- `bot/main.py` — entry point.
- `tests/` — pytest unit/integration tests with mocked HTTP and Telegram APIs.

## Security
- Bot token and OpenRouter key loaded from environment; never hardcoded or committed.
- Validate prompt length (max 1000 chars).
- Catch and log all exceptions; send only safe messages to users.
- Timeouts on all external HTTP calls.

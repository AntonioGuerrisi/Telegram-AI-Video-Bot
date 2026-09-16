# Telegram AI Video Bot

An async Telegram bot that generates videos from text prompts and images using the OpenRouter API with a prompt engineering layer.

## Features

- Text-to-video generation with prompt enhancement
- Image-to-video generation using a user-provided first frame
- Approval and editing flow for enhanced prompts
- Russian-language user interface
- English-language user interface (selected from the Telegram language)
- File-based logging per user
- Dockerized deployment

## Architecture

- `bot/handlers.py` — Telegram message and callback handlers
- `bot/keyboards.py` — inline keyboards for approval, editing, and new video
- `bot/openrouter_client.py` — OpenRouter video generation client with polling
- `bot/prompt_engineer.py` — prompt enhancement via Qwen
- `bot/translation_client.py` — translates the final prompt to Russian
- `bot/localization.py` — English and Russian user-facing messages
- `bot/config.py` — environment-based configuration
- `bot/logger.py` — application and per-user loggers

## Requirements

- Python 3.11+
- Docker and Docker Compose (recommended for deployment)
- A Telegram bot token
- OpenRouter API keys:
  - one for video generation
  - one for prompt engineering

## Configuration

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

```env
BOT_TOKEN=your_bot_token
OPENROUTER_API_KEY=your_openrouter_video_key
OPENROUTER_PROMPT_KEY=your_openrouter_prompt_key
LOG_LEVEL=INFO
```

## Local Development

Create a virtual environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows PowerShell, use Python 3.11 or 3.12 and activate the environment with:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

The bot uses Russian only when Telegram reports `ru` or `ru-*` as the user's language. English is the fallback for English, missing, and all other language codes.

Run the bot:

```bash
python -m bot.main
```

Run tests:

```bash
pytest
```

## Docker Deployment

Build and run with Docker Compose:

```bash
docker compose up --build -d
```

View logs:

```bash
docker compose logs -f
```

Stop the bot:

```bash
docker compose down
```

## Project Structure

```
.
├── bot/
│   ├── __init__.py
│   ├── config.py
│   ├── handlers.py
│   ├── keyboards.py
│   ├── logger.py
│   ├── localization.py
│   ├── main.py
│   ├── openrouter_client.py
│   ├── prompt_engineer.py
│   ├── prompts.py
│   └── translation_client.py
├── tests/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

## Publishing to GitHub

1. Initialize a Git repository if you haven't already:

```bash
git init
```

2. Create a `.gitignore` file:

```gitignore
.venv/
__pycache__/
*.pyc
.env
logs/
*.log
.DS_Store
.idea/
.vscode/
```

3. Add all project files except secrets and local artifacts:

```bash
git add .
```

4. Commit:

```bash
git commit -m "Initial commit: Telegram AI video bot"
```

5. Create a new empty repository on GitHub (do not initialize it with a README or `.gitignore`).

6. Add the remote and push:

```bash
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY_NAME.git
git branch -M main
git push -u origin main
```

Replace `YOUR_USERNAME` and `YOUR_REPOSITORY_NAME` with your actual GitHub username and repository name.

## Security Notes

- Never commit `.env` or any API keys to GitHub.
- Keep bot tokens and OpenRouter keys in environment variables only.
- The provided `.gitignore` excludes sensitive and generated files.

## License

MIT

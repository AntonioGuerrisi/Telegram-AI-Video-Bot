import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram import Dispatcher
from bot.config import Settings
from bot.handlers import (
    CLARIFICATION_MODE,
    EDIT_MODE,
    GENERATION_TASKS,
    PENDING_APPROVALS,
    register_handlers,
)


@pytest.fixture(autouse=True)
def clean_state():
    PENDING_APPROVALS.clear()
    EDIT_MODE.clear()
    CLARIFICATION_MODE.clear()
    GENERATION_TASKS.clear()
    yield


@pytest.fixture
def settings():
    return Settings(
        bot_token="test",
        openrouter_api_key="key",
        openrouter_prompt_key="prompt_key",
    )


@pytest.fixture
def mock_message():
    msg = MagicMock()
    msg.message_id = 1
    msg.from_user.id = 1
    msg.from_user.username = None
    msg.from_user.bot = MagicMock()
    msg.from_user.bot.send_message = AsyncMock(return_value=MagicMock())
    msg.chat.id = 1
    msg.text = "a cat dancing"
    msg.photo = None
    msg.document = None
    msg.caption = None
    progress_msg = MagicMock()
    progress_msg.message_id = 2
    progress_msg.from_user.id = 1
    progress_msg.chat.id = 1
    progress_msg.delete = AsyncMock()
    progress_msg.edit_text = AsyncMock()
    progress_msg.bot.send_message = AsyncMock(return_value=progress_msg)
    progress_msg.bot.send_video = AsyncMock()
    msg.from_user.bot.send_message = AsyncMock(return_value=progress_msg)
    msg.answer = AsyncMock(return_value=progress_msg)
    return msg


@pytest.fixture
def enhanced_prompt():
    return "Cinematic video of a dancing cat"


def _setup_engineer_mock(enhanced_prompt, is_clarification=False):
    instance = MagicMock()
    if is_clarification:
        content = "What style do you prefer?"
    else:
        content = f"Analysis\n```prompt\n{enhanced_prompt}\n```"
    instance.enhance_prompt = AsyncMock(return_value={"content": content})
    return patch("bot.handlers.PromptEngineerClient", return_value=instance)


@pytest.mark.asyncio
async def test_start_handler(mock_message):
    from bot.handlers import start_command
    await start_command(mock_message)
    assert mock_message.answer.called


@pytest.mark.asyncio
async def test_text_prompt_handler_creates_pending_approval(mock_message, settings, enhanced_prompt):
    patcher = _setup_engineer_mock(enhanced_prompt)
    with patcher, patch("bot.handlers._get_settings", return_value=settings), patch(
        "bot.handlers.PromptEngineerClient.extract_code_block", return_value=enhanced_prompt
    ):
        from bot.handlers import text_prompt_handler
        await text_prompt_handler(mock_message)
        assert 1 in PENDING_APPROVALS
        assert PENDING_APPROVALS[1]["enhanced_prompt"] == enhanced_prompt
        assert 1 not in CLARIFICATION_MODE


@pytest.mark.asyncio
async def test_text_prompt_handler_clarification_mode(mock_message, settings):
    patcher = _setup_engineer_mock("", is_clarification=True)
    with patcher, patch("bot.handlers._get_settings", return_value=settings), patch(
        "bot.handlers.PromptEngineerClient.extract_code_block", return_value=None
    ), patch("bot.handlers.PromptEngineerClient.is_clarification", return_value=True):
        from bot.handlers import text_prompt_handler
        await text_prompt_handler(mock_message)
        assert 1 in CLARIFICATION_MODE
        assert 1 in PENDING_APPROVALS


@pytest.mark.asyncio
async def test_clarification_answer_continues_conversation(mock_message, settings, enhanced_prompt):
    PENDING_APPROVALS[1] = {
        "chat_history": [
            {"role": "user", "content": "a cat dancing"},
            {"role": "assistant", "content": "What style?"},
        ],
        "image_data": None,
        "enhanced_prompt": "",
    }
    CLARIFICATION_MODE.add(1)
    mock_message.text = "cartoon style"

    patcher = _setup_engineer_mock(enhanced_prompt)
    with patcher, patch("bot.handlers._get_settings", return_value=settings), patch(
        "bot.handlers.PromptEngineerClient.extract_code_block", return_value=enhanced_prompt
    ):
        from bot.handlers import text_prompt_handler
        await text_prompt_handler(mock_message)
        assert 1 not in CLARIFICATION_MODE
        assert PENDING_APPROVALS[1]["enhanced_prompt"] == enhanced_prompt


@pytest.mark.asyncio
async def test_text_prompt_handler_empty_prompt(mock_message):
    mock_message.text = "   "
    from bot.handlers import text_prompt_handler
    await text_prompt_handler(mock_message)
    assert mock_message.answer.called


@pytest.mark.asyncio
async def test_text_prompt_handler_long_prompt(mock_message):
    mock_message.text = "a" * 1001
    from bot.handlers import text_prompt_handler
    await text_prompt_handler(mock_message)
    assert mock_message.answer.called


@pytest.mark.asyncio
async def test_generate_video_callback_starts_generation(settings, enhanced_prompt):
    PENDING_APPROVALS[1] = {
        "enhanced_prompt": enhanced_prompt,
        "image_data": None,
        "chat_history": [],
    }

    callback = MagicMock()
    callback.from_user.id = 1
    callback.answer = AsyncMock()
    callback.message.chat.id = 1
    callback.message.message_id = 3
    callback.message.from_user.id = 1
    callback.message.edit_reply_markup = AsyncMock()
    progress_msg = MagicMock()
    progress_msg.message_id = 4
    progress_msg.from_user.id = 1
    progress_msg.chat.id = 1
    progress_msg.delete = AsyncMock()
    progress_msg.edit_text = AsyncMock()
    progress_msg.bot.send_video = AsyncMock()
    progress_msg.bot.send_message = AsyncMock()
    callback.message.answer = AsyncMock(return_value=progress_msg)

    with patch("bot.handlers.OpenRouterClient") as MockClient, patch(
        "bot.handlers._get_settings", return_value=settings
    ):
        instance = MockClient.return_value
        instance.generate_video = AsyncMock(return_value="https://example.com/video.mp4")

        async def _create_file(url, path):
            with open(path, "wb"):
                pass

        instance.download_video = AsyncMock(side_effect=_create_file)
        from bot.handlers import generate_video_callback
        await generate_video_callback(callback)
        task = GENERATION_TASKS.pop((1, 4), None)
        assert task is not None
        await task
        assert progress_msg.bot.send_video.called


@pytest.mark.asyncio
async def test_image_prompt_handler_starts_generation(mock_message, settings):
    mock_message.photo = [MagicMock(file_id="photo-id")]
    mock_message.caption = "dancing cat"
    mock_message.bot.get_file = AsyncMock(return_value=MagicMock(file_path="photos/photo.jpg"))
    mock_message.bot.download_file = AsyncMock(return_value=b"image-bytes")

    progress_msg = mock_message.answer.return_value

    with patch("bot.handlers.PromptEngineerClient") as MockEngineer, patch(
        "bot.handlers.OpenRouterClient"
    ) as MockClient, patch("bot.handlers._get_settings", return_value=settings), patch(
        "bot.handlers.PromptEngineerClient.extract_code_block", return_value="animated cat prompt"
    ):
        engineer = MockEngineer.return_value
        engineer.enhance_prompt = AsyncMock(
            return_value={"content": "```text\nanimated cat prompt\n```"}
        )

        instance = MockClient.return_value
        instance.generate_video = AsyncMock(return_value="https://example.com/video.mp4")

        async def _create_file(url, path):
            with open(path, "wb"):
                pass

        instance.download_video = AsyncMock(side_effect=_create_file)
        from bot.handlers import image_prompt_handler
        await image_prompt_handler(mock_message)
        task = list(GENERATION_TASKS.values())[-1]
        assert task is not None
        await task
        assert progress_msg.bot.send_video.called


@pytest.mark.asyncio
async def test_edit_prompt_callback_starts_edit_mode(mock_message, settings):
    PENDING_APPROVALS[1] = {
        "enhanced_prompt": "test prompt",
        "image_data": None,
        "chat_history": [],
    }
    callback = MagicMock()
    callback.from_user.id = 1
    callback.answer = AsyncMock()
    callback.message = mock_message
    callback.message.edit_reply_markup = AsyncMock()

    from bot.handlers import edit_prompt_callback
    await edit_prompt_callback(callback)
    assert 1 in EDIT_MODE
    assert callback.message.answer.called


@pytest.mark.asyncio
async def test_edit_request_continues_conversation(mock_message, settings, enhanced_prompt):
    PENDING_APPROVALS[1] = {
        "chat_history": [
            {"role": "user", "content": "a cat dancing"},
            {"role": "assistant", "content": "```prompt\nold prompt\n```"},
        ],
        "image_data": None,
        "enhanced_prompt": "old prompt",
    }
    EDIT_MODE.add(1)
    mock_message.text = "make it cyberpunk"

    patcher = _setup_engineer_mock(enhanced_prompt)
    with patcher, patch("bot.handlers._get_settings", return_value=settings), patch(
        "bot.handlers.PromptEngineerClient.extract_code_block", return_value=enhanced_prompt
    ):
        from bot.handlers import text_prompt_handler
        await text_prompt_handler(mock_message)
        assert 1 not in EDIT_MODE
        assert PENDING_APPROVALS[1]["enhanced_prompt"] == enhanced_prompt


def test_register_handlers():
    dp = MagicMock(spec=Dispatcher)
    register_handlers(dp)
    assert dp.include_router.called

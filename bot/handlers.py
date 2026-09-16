import asyncio
import os
import shutil
import tempfile
from typing import Optional

from aiogram import Dispatcher, F, Router, types
from aiogram.filters import Command

from bot.config import Settings
from bot.keyboards import approve_prompt_keyboard, edit_mode_keyboard, new_video_keyboard
from bot.logger import get_user_logger, setup_app_logger
from bot.localization import get_locale
from bot.openrouter_client import OpenRouterClient, VideoGenerationError
from bot.prompt_engineer import PromptEngineerClient
from bot.prompts import PROMPT_ENGINEER_SYSTEM_PROMPT
from bot.translation_client import TranslationClient


router = Router()
GENERATION_TASKS = {}
PENDING_APPROVALS = {}
EDIT_MODE = set()
CLARIFICATION_MODE = set()
app_logger = setup_app_logger("INFO")


def register_handlers(dp: Dispatcher, settings: Settings | None = None):
    dp.include_router(router)


@router.message(Command("start"))
async def start_command(message: types.Message):
    _reset_user_state(message.from_user.id)
    _, messages = get_locale(getattr(message.from_user, "language_code", None))
    await message.answer(messages.start.format(example=messages.example))


@router.message(lambda msg: msg.text and not msg.text.startswith("/"))
async def text_prompt_handler(message: types.Message):
    user_id = message.from_user.id
    prompt = message.text.strip()

    if user_id in CLARIFICATION_MODE:
        await _process_clarification_answer(message, prompt)
    elif user_id in EDIT_MODE:
        await _process_edit_request(message, prompt)
    else:
        _reset_user_state(user_id)
        await _process_new_request(message, prompt)


@router.message(lambda msg: msg.photo)
async def image_prompt_handler(message: types.Message):
    user_id = message.from_user.id
    _reset_user_state(user_id)
    prompt = message.caption.strip() if message.caption else ""
    image_data = await _extract_image_data(message)
    await _process_new_request(message, prompt, image_data)


@router.message(lambda msg: msg.document and msg.document.mime_type and msg.document.mime_type.startswith("image/"))
async def document_image_prompt_handler(message: types.Message):
    user_id = message.from_user.id
    _reset_user_state(user_id)
    prompt = message.caption.strip() if message.caption else ""
    image_data = await _extract_image_data(message)
    await _process_new_request(message, prompt, image_data)


@router.callback_query(F.data == "generate_video")
async def generate_video_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    language_code = getattr(callback.from_user, "language_code", None)
    _, messages = get_locale(language_code)
    pending = PENDING_APPROVALS.pop(user_id, None)
    _reset_user_state(user_id)

    if not pending:
        await callback.answer(messages.stale_session, show_alert=True)
        return

    await callback.answer(messages.generate_started)
    await callback.message.edit_reply_markup(reply_markup=None)

    progress_msg = await callback.message.answer(
        messages.generating_approved
    )

    task = asyncio.create_task(
        _generate_and_send(
            chat_id=callback.message.chat.id,
            progress_msg=progress_msg,
            prompt=pending["enhanced_prompt"],
            image_data=pending.get("image_data"),
            language_code=language_code,
        )
    )
    GENERATION_TASKS[(user_id, progress_msg.message_id)] = task


@router.callback_query(F.data == "edit_prompt")
async def edit_prompt_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    _, messages = get_locale(getattr(callback.from_user, "language_code", None))
    pending = PENDING_APPROVALS.get(user_id)
    if not pending:
        await callback.answer(messages.stale_session, show_alert=True)
        return

    CLARIFICATION_MODE.discard(user_id)
    EDIT_MODE.add(user_id)
    await callback.answer(messages.edit_mode)
    edit_msg = await callback.message.answer(
        messages.edit_prompt,
        reply_markup=edit_mode_keyboard(getattr(callback.from_user, "language_code", None)),
    )
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer(
        messages.waiting_edits,
        reply_to_message_id=edit_msg.message_id,
    )


@router.callback_query(F.data == "new_video")
async def new_video_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    _, messages = get_locale(getattr(callback.from_user, "language_code", None))
    _reset_user_state(user_id)
    await callback.answer(messages.new_generation)
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer(
        messages.new_video.format(example=messages.example)
    )


@router.callback_query(F.data == "cancel_edit")
async def cancel_edit_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    _, messages = get_locale(getattr(callback.from_user, "language_code", None))
    EDIT_MODE.discard(user_id)
    await callback.answer(messages.cancel_edit)
    await callback.message.edit_reply_markup(reply_markup=None)
    pending = PENDING_APPROVALS.get(user_id)
    if pending and pending.get("enhanced_prompt"):
        await callback.message.answer(
            f"{messages.perfect_prompt}\n"
            f"```text\n{pending['enhanced_prompt']}\n```",
            reply_markup=approve_prompt_keyboard(getattr(callback.from_user, "language_code", None)),
            parse_mode="Markdown",
        )


async def _process_new_request(
    message: types.Message,
    prompt: str,
    image_data: Optional[bytes] = None,
):
    user = message.from_user
    user_id = user.id
    _, messages = get_locale(getattr(user, "language_code", None))

    if not prompt:
        await message.answer(messages.empty_prompt)
        return

    if len(prompt) > 1000:
        await message.answer(messages.prompt_too_long)
        return

    if image_data:
        await _process_image_request(
            user=user,
            chat_id=message.chat.id,
            prompt=prompt,
            image_data=image_data,
        )
        return

    progress_msg = await message.answer(messages.thinking)
    await _enhance_prompt(
        user_id=user_id,
        username=user.username,
        chat_id=message.chat.id,
        progress_msg=progress_msg,
        user_request=prompt,
        chat_history=None,
        image_data=None,
        language_code=getattr(user, "language_code", None),
    )


async def _process_image_request(
    user: types.User,
    chat_id: int,
    prompt: str,
    image_data: bytes,
):
    user_id = user.id
    language_code = getattr(user, "language_code", None)
    _, messages = get_locale(language_code)
    user_logger = get_user_logger(user_id)
    app_logger.info("User %s (%s) requested image-to-video: %s", user_id, user.username, prompt)
    user_logger.info("Image-to-video request: %s", prompt)

    settings = _get_settings()
    client = OpenRouterClient(settings.openrouter_api_key)

    bot = user.bot
    progress_msg = await bot.send_message(
        chat_id,
        messages.image_generating,
    )

    task = asyncio.create_task(
        _generate_and_send(
            chat_id=chat_id,
            progress_msg=progress_msg,
            prompt=prompt,
            image_data=image_data,
            language_code=language_code,
        )
    )
    GENERATION_TASKS[(user_id, progress_msg.message_id)] = task


async def _process_clarification_answer(
    message: types.Message,
    prompt: str,
):
    user = message.from_user
    user_id = user.id
    language_code = getattr(user, "language_code", None)
    _, messages = get_locale(language_code)
    pending = PENDING_APPROVALS.get(user_id)

    if not pending:
        CLARIFICATION_MODE.discard(user_id)
        await message.answer(messages.stale_session)
        return

    progress_msg = await message.answer(messages.thinking)
    chat_history = pending["chat_history"]
    chat_history.append({"role": "user", "content": prompt})

    await _enhance_prompt(
        user_id=user_id,
        username=user.username,
        chat_id=message.chat.id,
        progress_msg=progress_msg,
        user_request=prompt,
        chat_history=chat_history[:-1],
        image_data=pending.get("image_data"),
        language_code=language_code,
    )


async def _process_edit_request(
    message: types.Message,
    prompt: str,
):
    user = message.from_user
    user_id = user.id
    language_code = getattr(user, "language_code", None)
    _, messages = get_locale(language_code)
    pending = PENDING_APPROVALS.get(user_id)

    if not pending:
        EDIT_MODE.discard(user_id)
        await message.answer(messages.stale_session)
        return

    progress_msg = await message.answer(messages.thinking)
    chat_history = pending["chat_history"]
    edit_message = f"Измени промпт: {prompt}"
    chat_history.append({"role": "user", "content": edit_message})

    await _enhance_prompt(
        user_id=user_id,
        username=user.username,
        chat_id=message.chat.id,
        progress_msg=progress_msg,
        user_request=edit_message,
        chat_history=chat_history[:-1],
        image_data=pending.get("image_data"),
        language_code=language_code,
    )


async def _enhance_prompt(
    user_id: int,
    username: Optional[str],
    chat_id: int,
    progress_msg: types.Message,
    user_request: str,
    chat_history: Optional[list[dict]],
    image_data: Optional[bytes] = None,
    language_code: str | None = None,
):
    locale, messages = get_locale(language_code)
    user_logger = get_user_logger(user_id)
    app_logger.info("User %s (%s) requested prompt engineering: %s", user_id, username, user_request)
    user_logger.info("Prompt engineering request: %s", user_request)

    try:
        settings = _get_settings()
        engineer = PromptEngineerClient(settings.openrouter_prompt_key)
        result = await engineer.enhance_prompt(
            user_prompt=user_request,
            system_prompt=PROMPT_ENGINEER_SYSTEM_PROMPT,
            chat_history=chat_history,
            image_data=image_data,
        )
        enhanced = result["content"]

        current_history = list(chat_history) if chat_history else []
        current_history.append({"role": "assistant", "content": enhanced})

        enhanced_prompt = PromptEngineerClient.extract_code_block(enhanced)
        is_clarification = PromptEngineerClient.is_clarification(enhanced) and enhanced_prompt is None

        if is_clarification:
            CLARIFICATION_MODE.add(user_id)
            EDIT_MODE.discard(user_id)
            PENDING_APPROVALS[user_id] = {
                "chat_history": current_history,
                "image_data": image_data,
                "enhanced_prompt": "",
                "language_code": language_code,
            }
            await progress_msg.delete()
            await progress_msg.bot.send_message(
                chat_id=chat_id,
                text=messages.clarification.format(content=enhanced),
            )
            return

        CLARIFICATION_MODE.discard(user_id)
        EDIT_MODE.discard(user_id)

        if not enhanced_prompt:
            enhanced_prompt = enhanced.strip()

        settings = _get_settings()
        translator = TranslationClient(settings.openrouter_prompt_key)
        try:
            translation = (
                await translator.translate_to_russian(enhanced_prompt)
                if locale == "ru"
                else enhanced_prompt
            )
        except Exception:
            app_logger.exception("Translation failed for user %s", user_id)
            translation = messages.translation_failed

        PENDING_APPROVALS[user_id] = {
            "chat_history": current_history,
            "image_data": image_data,
            "enhanced_prompt": enhanced_prompt,
            "language_code": language_code,
        }

        await progress_msg.delete()
        await progress_msg.bot.send_message(
            chat_id=chat_id,
            text=(
                f"{messages.perfect_prompt}\n```text\n{enhanced_prompt}\n```\n\n"
                f"{messages.russian_translation if locale == 'ru' else messages.prompt_language}:\n{translation}"
            ),
            reply_markup=approve_prompt_keyboard(language_code),
            parse_mode="Markdown",
        )

    except Exception as exc:
        app_logger.exception("Error enhancing prompt for user %s", user_id)
        user_logger.error("Error: %s", exc)
        await progress_msg.edit_text(
            messages.enhancement_error
        )


async def _extract_image_data(message: types.Message) -> Optional[bytes]:
    image_data = None
    if message.photo:
        photo = message.photo[-1]
        file = await message.bot.get_file(photo.file_id)
        image_bytesio = await message.bot.download_file(file.file_path)
        image_data = image_bytesio.read() if hasattr(image_bytesio, "read") else image_bytesio
    elif message.document and message.document.mime_type and message.document.mime_type.startswith("image/"):
        file = await message.bot.get_file(message.document.file_id)
        image_bytesio = await message.bot.download_file(file.file_path)
        image_data = image_bytesio.read() if hasattr(image_bytesio, "read") else image_bytesio
    return image_data


async def _generate_and_send(
    chat_id: int,
    progress_msg: types.Message,
    prompt: str,
    image_data: Optional[bytes] = None,
    language_code: str | None = None,
):
    user_id = progress_msg.from_user.id if progress_msg.from_user else chat_id
    _, messages = get_locale(language_code or getattr(progress_msg.from_user, "language_code", None))
    user_logger = get_user_logger(user_id)

    try:
        settings = _get_settings()
        client = OpenRouterClient(settings.openrouter_api_key)
        video_url = await client.generate_video(prompt, user_id, image_data)

        tmpdir = tempfile.mkdtemp()
        video_path = os.path.join(tmpdir, "video.mp4")
        try:
            await client.download_video(video_url, video_path)

            await progress_msg.bot.send_video(
                chat_id=chat_id,
                video=types.FSInputFile(video_path),
                caption=messages.video_ready,
            )

            await progress_msg.delete()
            user_logger.info("Success: video sent from %s", video_url)

            await progress_msg.bot.send_message(
                chat_id=chat_id,
                 text=messages.new_video.format(example=messages.example),
                 reply_markup=new_video_keyboard(language_code),
            )
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)
    except VideoGenerationError as exc:
        app_logger.exception("Video generation error for user %s", user_id)
        user_logger.error("Error: %s", exc)
        if exc.is_ip_infringement:
            error_text = messages.ip_error
        else:
            error_text = messages.generation_error
        await progress_msg.edit_text(error_text)
    except Exception as exc:
        app_logger.exception("Error generating video for user %s", user_id)
        user_logger.error("Error: %s", exc)
        await progress_msg.edit_text(
            messages.generation_error
        )
    finally:
        GENERATION_TASKS.pop((user_id, progress_msg.message_id), None)


def _get_settings() -> Settings:
    from bot.config import load_settings
    return load_settings()


def _reset_user_state(user_id: int):
    PENDING_APPROVALS.pop(user_id, None)
    EDIT_MODE.discard(user_id)
    CLARIFICATION_MODE.discard(user_id)


async def cancel_pending_tasks():
    pending = list(GENERATION_TASKS.values())
    if not pending:
        return
    for task in pending:
        task.cancel()
    await asyncio.gather(*pending, return_exceptions=True)
    GENERATION_TASKS.clear()

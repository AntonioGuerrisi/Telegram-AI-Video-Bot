from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.localization import get_locale


def approve_prompt_keyboard(language_code: str | None = None) -> InlineKeyboardMarkup:
    _, messages = get_locale(language_code)
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=f"✨ {messages.approve_video}", callback_data="generate_video"),
                InlineKeyboardButton(text=f"✏️ {messages.edit_button}", callback_data="edit_prompt"),
            ],
            [
                InlineKeyboardButton(text=f"🆕 {messages.new_video_button}", callback_data="new_video"),
            ],
        ]
    )


def edit_mode_keyboard(language_code: str | None = None) -> InlineKeyboardMarkup:
    _, messages = get_locale(language_code)
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"❌ {messages.cancel_button}", callback_data="cancel_edit")]
        ]
    )


def new_video_keyboard(language_code: str | None = None) -> InlineKeyboardMarkup:
    _, messages = get_locale(language_code)
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"🎬 {messages.new_video_button}", callback_data="new_video")]
        ]
    )

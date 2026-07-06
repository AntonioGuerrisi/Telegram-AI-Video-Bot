from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def approve_prompt_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✨ Сгенерировать видео", callback_data="generate_video"),
                InlineKeyboardButton(text="✏️ Изменить", callback_data="edit_prompt"),
            ],
            [
                InlineKeyboardButton(text="🆕 Новое видео", callback_data="new_video"),
            ],
        ]
    )


def edit_mode_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отменить редактирование", callback_data="cancel_edit")]
        ]
    )


def new_video_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎬 Создать новое видео", callback_data="new_video")]
        ]
    )

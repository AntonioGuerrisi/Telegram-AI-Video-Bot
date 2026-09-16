from bot.keyboards import approve_prompt_keyboard, edit_mode_keyboard, new_video_keyboard
from bot.localization import get_locale


def test_english_locale_and_region_code():
    locale, messages = get_locale("en-US")
    assert locale == "en"
    assert messages.empty_prompt == "Please describe the video."


def test_unknown_locale_falls_back_to_english():
    locale, messages = get_locale("it")
    assert locale == "en"
    assert messages.empty_prompt == "Please describe the video."


def test_missing_locale_falls_back_to_english():
    locale, messages = get_locale(None)
    assert locale == "en"
    assert messages.empty_prompt == "Please describe the video."


def test_english_keyboard_labels():
    approve = approve_prompt_keyboard("en")
    edit = edit_mode_keyboard("en")
    new_video = new_video_keyboard("en")

    assert approve.inline_keyboard[0][0].text == "✨ Generate video"
    assert approve.inline_keyboard[0][1].text == "✏️ Edit"
    assert edit.inline_keyboard[0][0].text == "❌ Cancel editing"
    assert new_video.inline_keyboard[0][0].text == "🎬 New video"

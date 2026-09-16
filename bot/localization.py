from dataclasses import dataclass


@dataclass(frozen=True)
class Messages:
    start: str
    example: str
    stale_session: str
    generate_started: str
    approve_video: str
    generating_approved: str
    edit_mode: str
    edit_button: str
    edit_prompt: str
    waiting_edits: str
    new_generation: str
    new_video_button: str
    new_video: str
    cancel_edit: str
    cancel_button: str
    empty_prompt: str
    prompt_too_long: str
    thinking: str
    image_generating: str
    clarification: str
    clarification_reply: str
    perfect_prompt: str
    russian_translation: str
    prompt_language: str
    translation_failed: str
    enhancement_error: str
    video_ready: str
    ip_error: str
    generation_error: str


_MESSAGES = {
    "ru": Messages(
        start=(
            "Привет! Я бот для генерации видео.\n\n"
            "Просто отправь мне текстовый запрос — и я подготовлю идеальный промпт и создам короткое видео.\n"
            "Или загрузи изображение с подписью, и я сделаю видео на его основе.\n\n"
            "Пример:\n{example}"
        ),
        example="кот танцует под дождем",
        stale_session="Сессия устарела. Начните заново.",
        generate_started="Начинаю генерацию видео...",
        approve_video="Сгенерировать видео",
        generating_approved="Генерирую видео по согласованному промпту... Это может занять несколько минут.",
        edit_mode="Режим редактирования",
        edit_button="Изменить",
        edit_prompt="Напишите, что нужно изменить в промпте:",
        waiting_edits="Жду ваши правки...",
        new_generation="Новая генерация",
        new_video_button="Новое видео",
        new_video="Вы можете создать ещё видео. Введите текстовый запрос для генерации видео.\n\nПример:\n{example}",
        cancel_edit="Редактирование отменено",
        cancel_button="Отменить редактирование",
        empty_prompt="Пожалуйста, напишите описание видео.",
        prompt_too_long="Описание слишком длинное. Максимум 1000 символов.",
        thinking="Думаю над идеальным промптом...",
        image_generating="Генерирую видео по вашей картинке... Это может занять несколько минут.",
        clarification="Уточнение:\n\n{content}\n\nНапишите ответ в чат.",
        clarification_reply="Перевод на русский:\n{translation}",
        perfect_prompt="Идеальный промпт:",
        russian_translation="Перевод на русский:",
        prompt_language="Язык промпта:",
        translation_failed="(Не удалось получить перевод)",
        enhancement_error="Произошла ошибка при обработке запроса. Попробуйте позже или измените описание.",
        video_ready="Ваше видео готово!",
        ip_error=(
            "Не удалось сгенерировать видео: запрос может нарушать права на интеллектуальную собственность "
            "(упоминание реальных людей, персонажей или брендов). Попробуйте изменить промпт, "
            "используя вымышленных персонажей или общие описания."
        ),
        generation_error="Произошла ошибка при генерации видео. Попробуйте позже или измените запрос.",
    ),
    "en": Messages(
        start=(
            "Hi! I am a video generation bot.\n\n"
            "Send me a text prompt and I will prepare the perfect prompt and create a short video.\n"
            "Or upload an image with a caption and I will turn it into a video.\n\n"
            "Example:\n{example}"
        ),
        example="a cat dancing in the rain",
        stale_session="This session has expired. Please start again.",
        generate_started="Starting video generation...",
        approve_video="Generate video",
        generating_approved="Generating a video from the approved prompt... This may take a few minutes.",
        edit_mode="Edit mode",
        edit_button="Edit",
        edit_prompt="Tell me what you would like to change in the prompt:",
        waiting_edits="Waiting for your changes...",
        new_generation="New generation",
        new_video_button="New video",
        new_video="You can create another video. Enter a text prompt to generate a video.\n\nExample:\n{example}",
        cancel_edit="Editing cancelled",
        cancel_button="Cancel editing",
        empty_prompt="Please describe the video.",
        prompt_too_long="The description is too long. The maximum is 1000 characters.",
        thinking="Thinking about the perfect prompt...",
        image_generating="Generating a video from your image... This may take a few minutes.",
        clarification="Clarification:\n\n{content}\n\nPlease reply in the chat.",
        clarification_reply="English translation:\n{translation}",
        perfect_prompt="Perfect prompt:",
        russian_translation="Russian translation:",
        prompt_language="Prompt language:",
        translation_failed="(Translation unavailable)",
        enhancement_error="Something went wrong while processing your request. Please try again or change the description.",
        video_ready="Your video is ready!",
        ip_error=(
            "The video could not be generated: the request may violate intellectual property rights "
            "(real people, characters, or brands). Try changing the prompt to use fictional characters "
            "or general descriptions."
        ),
        generation_error="Something went wrong while generating the video. Please try again or change the prompt.",
    ),
}


def get_locale(language_code: str | None) -> tuple[str, Messages]:
    if not isinstance(language_code, str):
        language_code = "en"
    language = language_code.lower().split("-", 1)[0].split("_", 1)[0]
    locale = language if language in _MESSAGES else "en"
    return locale, _MESSAGES[locale]

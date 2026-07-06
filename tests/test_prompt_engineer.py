import pytest
from bot.prompt_engineer import PromptEngineerClient


def test_extract_code_block_with_prompt_label():
    content = "Analysis\n```prompt\nA cat dancing in the rain\n```"
    result = PromptEngineerClient.extract_code_block(content)
    assert result == "A cat dancing in the rain"


def test_extract_code_block_without_label():
    content = "Analysis\n```\nA cat dancing in the rain\n```"
    result = PromptEngineerClient.extract_code_block(content)
    assert result == "A cat dancing in the rain"


def test_extract_code_block_not_found():
    content = "Just plain text without code block"
    result = PromptEngineerClient.extract_code_block(content)
    assert result is None


def test_is_clarification_question():
    assert PromptEngineerClient.is_clarification("What style do you prefer?") is True


def test_is_clarification_code_block():
    assert PromptEngineerClient.is_clarification("```prompt\ncat\n```") is False


def test_is_clarification_statement():
    assert PromptEngineerClient.is_clarification("Here is your final prompt.") is False

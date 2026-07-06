import logging
import os
import shutil
import pytest
from bot.logger import setup_app_logger, get_user_logger


@pytest.fixture
def temp_logs(tmp_path, monkeypatch):
    logs_dir = tmp_path / "logs"
    monkeypatch.setattr("bot.logger.LOGS_DIR", str(logs_dir))
    yield logs_dir
    shutil.rmtree(logs_dir, ignore_errors=True)


def test_setup_app_logger(temp_logs):
    logger = setup_app_logger("INFO")
    assert logger.level == logging.INFO
    assert any(isinstance(h, logging.FileHandler) for h in logger.handlers)


def test_get_user_logger(temp_logs):
    logger = get_user_logger(12345)
    assert logger.name == "user_12345"
    assert any(isinstance(h, logging.FileHandler) for h in logger.handlers)

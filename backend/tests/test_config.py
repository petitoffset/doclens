import os
from pathlib import Path

import pytest

from app.config import ENV_PATH, load_environment


def test_default_environment_path_is_repository_root() -> None:
    assert ENV_PATH == Path(__file__).resolve().parents[2] / ".env"


def test_load_environment_reads_explicit_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("DOCLENS_TEST_SETTING=from-file\n", encoding="utf-8")
    monkeypatch.delenv("DOCLENS_TEST_SETTING", raising=False)

    load_environment(env_file)

    assert os.environ["DOCLENS_TEST_SETTING"] == "from-file"


def test_process_environment_takes_precedence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("DOCLENS_TEST_SETTING=from-file\n", encoding="utf-8")
    monkeypatch.setenv("DOCLENS_TEST_SETTING", "from-process")

    load_environment(env_file)

    assert os.environ["DOCLENS_TEST_SETTING"] == "from-process"

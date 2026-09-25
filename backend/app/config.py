"""Local environment configuration for DocLens."""

from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = PROJECT_ROOT / ".env"


def load_environment(path: Path = ENV_PATH) -> None:
    """Load local defaults without overriding the process environment."""

    load_dotenv(dotenv_path=path, override=False)

"""Application configuration using pycore ConfigManager."""

from pathlib import Path
from typing import Any

from pydantic import Field

from pycore.core import BaseSettings, ConfigManager
from pycore.core.config import ConfigLoader

BACKEND_DIR = Path(__file__).parent.parent.parent


class DotEnvConfigLoader(ConfigLoader):
    """Load KEY=VALUE pairs from a .env file."""

    def supports(self, path: Path) -> bool:
        return path.name.lower() == ".env" or path.suffix.lower() == ".env"

    def load(self, path: Path) -> dict[str, Any]:
        data: dict[str, Any] = {}
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            key, _, value = line.partition("=")
            key = key.strip().lower()
            value = value.strip().strip('"').strip("'")
            if key:
                data[key] = value
        return data


class Settings(BaseSettings):
    """Application settings loaded from backend/.env."""

    dashscope_api_key: str
    llm_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    llm_model: str = "qwen-plus"
    embedding_model: str = "text-embedding-v3"
    rerank_model: str = "gte-rerank"

    database_url: str = "sqlite+aiosqlite:///./data/app.db"
    upload_dir: str = "./uploads"

    jwt_secret: str = Field(..., min_length=8)
    jwt_expire_hours: int = 24
    api_port: int = 8099

    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5199",
            "http://127.0.0.1:5199",
            "http://localhost:5175",
            "http://127.0.0.1:5175",
        ]
    )

    @property
    def data_dir(self) -> Path:
        """Get data directory path."""
        if self.database_url.startswith("sqlite"):
            db_path = self.database_url.split("///")[-1]
            return Path(db_path).parent
        return Path("./data")


_config = ConfigManager[Settings]()
_config.register_loader(DotEnvConfigLoader())
_config.load(Settings, BACKEND_DIR / ".env")
settings = _config.settings

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "stock-flow.db"


class Settings(BaseSettings):
    app_name: str = "资金流透镜"
    database_url: str = f"sqlite:///{DEFAULT_DB_PATH}"
    eastmoney_timeout_seconds: float = 12.0
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    model_config = SettingsConfigDict(env_file=".env", env_prefix="STOCK_FLOW_")


settings = Settings()

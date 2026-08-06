from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    anthropic_api_key: str = ""
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    google_credentials_path: Path = Path("./credentials.json")
    google_sheets_id: str = ""
    chrome_profile_path: str = ""
    database_path: Path = Path("./data/agent_office.db")
    cache_ttl_seconds: int = 3600
    default_model: str = "claude-sonnet-4-20250514"
    complex_model: str = "claude-sonnet-4-20250514"
    log_level: str = "INFO"
    port: int = 8000

    def ensure_data_dir(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)


settings = Settings()


if __name__ == "__main__":
    from pprint import pprint
    settings.ensure_data_dir()
    pprint(settings.model_dump())

from uuid import UUID

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """アプリケーション設定。環境変数から読み込む。"""

    database_url: str = "postgresql+psycopg://memo:memo@db:5432/memo_app"
    default_user_id: UUID = UUID("00000000-0000-0000-0000-000000000001")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()

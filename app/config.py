from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    bot_token: str = Field(default="", alias="BOT_TOKEN")
    bot_username: str = Field(default="your_support_bot", alias="BOT_USERNAME")
    bot_language: str = Field(default="ru", alias="BOT_LANGUAGE")

    sqlite_path: str = Field(default="data/kb.sqlite3", alias="SQLITE_PATH")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    support_usernames: str = Field(default="tgtaps_support,admin", alias="SUPPORT_USERNAMES")
    group_antispam_ttl_sec: int = Field(default=900, alias="GROUP_ANTISPAM_TTL_SEC")
    min_confidence: float = Field(default=55.0, alias="MIN_CONFIDENCE")
    ambiguity_delta: float = Field(default=8.0, alias="AMBIGUITY_DELTA")

    docs_base_url: str = Field(default="https://docs.tgtaps.com/tgtaps-docs", alias="DOCS_BASE_URL")
    docs_max_pages: int = Field(default=80, alias="DOCS_MAX_PAGES")
    docs_max_depth: int = Field(default=3, alias="DOCS_MAX_DEPTH")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def support_usernames_set(self) -> set[str]:
        return {x.strip().lower().lstrip("@") for x in self.support_usernames.split(",") if x.strip()}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

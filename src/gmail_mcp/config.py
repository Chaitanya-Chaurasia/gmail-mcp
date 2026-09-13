"""Settings loaded from environment / .env via pydantic-settings."""

from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

GMAIL_SCOPES = [
    # modify covers read + trash + labels; send is for mailto: unsubscribes;
    # settings.basic is for block_sender filters. Deliberately NOT the full
    # mail.google.com scope - no permanent delete for an AI agent.
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.settings.basic",
]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="GMAIL_MCP_", env_file=".env", env_file_encoding="utf-8"
    )

    credentials_path: Path = Path("credentials.json")
    token_path: Path = Path("~/.gmail-mcp-token.json")
    max_results_cap: int = 50
    body_char_limit: int = 10_000

    @field_validator("credentials_path", "token_path")
    @classmethod
    def _expand(cls, v: Path) -> Path:
        return v.expanduser()


settings = Settings()

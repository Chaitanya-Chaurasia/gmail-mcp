"""OAuth flow and Gmail service construction."""

from functools import lru_cache

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from gmail_mcp.config import GMAIL_SCOPES, settings


def _load_credentials() -> Credentials:
    creds = None
    if settings.token_path.exists():
        creds = Credentials.from_authorized_user_file(str(settings.token_path), GMAIL_SCOPES)
    if creds and creds.valid:
        return creds
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        if not settings.credentials_path.exists():
            raise RuntimeError(
                f"Missing {settings.credentials_path}. Download an OAuth Desktop-app "
                "client from Google Cloud Console (Gmail API enabled), or point "
                "GMAIL_MCP_CREDENTIALS_PATH at it. Then run: gmail-mcp --login"
            )
        flow = InstalledAppFlow.from_client_secrets_file(
            str(settings.credentials_path), GMAIL_SCOPES
        )
        creds = flow.run_local_server(port=0)
    settings.token_path.write_text(creds.to_json())
    return creds


@lru_cache(maxsize=1)
def gmail_service():
    """Build (and cache) the Gmail API service client."""
    return build("gmail", "v1", credentials=_load_credentials())

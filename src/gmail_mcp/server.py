"""Entry point: `gmail-mcp` (stdio server) or `gmail-mcp --login` (OAuth)."""

import sys

import gmail_mcp.tools  # noqa: F401  - importing registers all tools
from gmail_mcp.app import mcp
from gmail_mcp.auth import gmail_service
from gmail_mcp.config import settings


def main() -> None:
    if "--login" in sys.argv:
        gmail_service()
        print(f"OAuth complete. Token saved to {settings.token_path}")
    else:
        mcp.run()


if __name__ == "__main__":
    main()

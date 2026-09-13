"""Cleanup tools: trash and spam. All recoverable - no permanent delete."""

from gmail_mcp import gmail
from gmail_mcp.app import mcp


@mcp.tool()
def trash_email(message_id: str) -> str:
    """Move one email to Trash (recoverable in Gmail for 30 days)."""
    gmail.trash(message_id)
    return f"Moved {message_id} to trash."


@mcp.tool()
def trash_many(message_ids: list[str]) -> str:
    """Move up to 1000 emails to Trash in one batch (recoverable for 30 days).

    Args:
        message_ids: message IDs, e.g. from search_emails results.
    """
    n = gmail.trash_batch(message_ids)
    return f"Moved {n} messages to trash."


@mcp.tool()
def report_spam(message_id: str) -> str:
    """Mark a message as spam - moves it to Spam and trains Gmail's filter."""
    gmail.mark_spam(message_id)
    return f"Reported {message_id} as spam."

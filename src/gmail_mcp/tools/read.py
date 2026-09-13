"""Read-only tools: search, read, thread, labels."""

from gmail_mcp import gmail
from gmail_mcp.app import mcp
from gmail_mcp.config import settings


@mcp.tool()
def search_emails(query: str, max_results: int = 15) -> str:
    """Search Gmail and return a compact list of matching messages.

    Args:
        query: Gmail search syntax, e.g. 'from:foo@bar.com is:unread',
            'category:promotions older_than:6m', 'in:spam newer_than:7d',
            'unsubscribe older_than:1y'.
        max_results: max messages to return (1-50).
    """
    return gmail.search(query, max_results).render()


@mcp.tool()
def read_email(message_id: str) -> str:
    """Read the full plain-text body of one email by message ID."""
    return gmail.read(message_id).render(settings.body_char_limit)


@mcp.tool()
def get_thread(thread_id: str) -> str:
    """List every message in a conversation thread (metadata only)."""
    messages = gmail.thread(thread_id)
    return "\n".join(m.render() for m in messages) or "Empty thread."


@mcp.tool()
def list_labels() -> str:
    """List all Gmail labels with their unread/total message counts."""
    return "\n".join(lb.render() for lb in gmail.labels())

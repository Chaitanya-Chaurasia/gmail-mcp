"""Unsubscribe tools: inspect List-Unsubscribe, act on mailto:, block senders.

Policy: only mailto: unsubscribes are acted on automatically. Bare URLs are
returned for the human - fetching unsubscribe links from spam confirms the
address is live.
"""

from gmail_mcp import gmail
from gmail_mcp.app import mcp


@mcp.tool()
def get_unsubscribe_info(message_id: str) -> str:
    """Extract the List-Unsubscribe method from an email, if the sender offers one.

    Returns the mailto: address and/or URL, and whether one-click POST
    (RFC 8058) is supported. Prefer mailto: via send_unsubscribe; only
    show URLs to the user, never fetch them.
    """
    return gmail.unsubscribe_info(message_id).render()


@mcp.tool()
def send_unsubscribe(mailto_address: str, subject: str = "unsubscribe") -> str:
    """Send an unsubscribe email to a mailto: address from get_unsubscribe_info.

    Args:
        mailto_address: bare address only (no 'mailto:' prefix or query params).
        subject: subject line; some senders require the word 'unsubscribe'.
    """
    addr = mailto_address.removeprefix("mailto:").split("?")[0]
    gmail.send_message(to=addr, subject=subject)
    return f"Sent unsubscribe email to {addr}."


@mcp.tool()
def block_sender(sender_email: str) -> str:
    """Create a Gmail filter that auto-trashes all future mail from a sender.

    Use when a sender has no working unsubscribe or keeps mailing anyway.
    """
    gmail.create_block_filter(sender_email)
    return f"Created filter: all future mail from {sender_email} goes to trash."

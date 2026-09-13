"""Gmail MCP server — inbox cleanup toolkit.

Tools:
  search_emails         - search with Gmail query syntax (read)
  read_email            - full body of one message (read)
  get_thread            - all messages in a conversation (read)
  trash_email           - move one message to Trash (recoverable)
  trash_many            - batch-trash up to 1000 message IDs
  report_spam           - mark a message as spam (trains Gmail's filter)
  list_labels           - list all labels with message counts
  get_unsubscribe_info  - extract List-Unsubscribe header from a message
  send_unsubscribe      - act on a mailto: unsubscribe address
  block_sender          - create a filter that auto-trashes a sender

First run: `python gmail_mcp.py --login` to complete the OAuth flow in a
browser. After that, register with Claude Code:
  claude mcp add gmail -- python /Users/chait/Desktop/gmail-mcp/gmail_mcp.py
"""

import base64
import sys
from email.mime.text import MIMEText
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# gmail.modify covers read + trash + labels. send is only for mailto:
# unsubscribes; settings.basic is only for block_sender filters.
SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.settings.basic",
]
TOKEN = Path.home() / ".gmail-mcp-token.json"
CREDS = Path(__file__).parent / "credentials.json"

mcp = FastMCP("gmail")


def gmail_service():
    creds = None
    if TOKEN.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDS.exists():
                raise RuntimeError(
                    f"Missing {CREDS}. Download an OAuth Desktop-app client "
                    "from Google Cloud Console (Gmail API enabled) first."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDS), SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN.write_text(creds.to_json())
    return build("gmail", "v1", credentials=creds)


def _headers(msg) -> dict:
    return {h["name"]: h["value"] for h in msg["payload"]["headers"]}


# ---------------------------------------------------------------- read tools

@mcp.tool()
def search_emails(query: str, max_results: int = 15) -> str:
    """Search Gmail and return a compact list of matching messages.

    Args:
        query: Gmail search syntax, e.g. 'from:foo@bar.com is:unread',
            'category:promotions older_than:6m', 'in:spam newer_than:7d',
            'unsubscribe older_than:1y'.
        max_results: max messages to return (1-50).
    """
    svc = gmail_service()
    resp = (
        svc.users()
        .messages()
        .list(userId="me", q=query, maxResults=max(1, min(max_results, 50)))
        .execute()
    )
    msgs = resp.get("messages", [])
    if not msgs:
        return "No messages found."
    out = []
    for m in msgs:
        msg = (
            svc.users()
            .messages()
            .get(
                userId="me",
                id=m["id"],
                format="metadata",
                metadataHeaders=["From", "Subject", "Date"],
            )
            .execute()
        )
        h = _headers(msg)
        out.append(
            f"[{m['id']}] {h.get('Date', '?')} | {h.get('From', '?')} | "
            f"{h.get('Subject', '(no subject)')}"
        )
    more = f"\n(estimated total matches: {resp.get('resultSizeEstimate')})"
    return "\n".join(out) + more


@mcp.tool()
def read_email(message_id: str) -> str:
    """Read the full plain-text body of one email by message ID."""
    svc = gmail_service()
    msg = (
        svc.users().messages().get(userId="me", id=message_id, format="full").execute()
    )

    def extract(part) -> str:
        if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
            return base64.urlsafe_b64decode(part["body"]["data"]).decode(
                errors="replace"
            )
        return "".join(extract(p) for p in part.get("parts", []))

    h = _headers(msg)
    body = extract(msg["payload"]) or "(no plain-text body)"
    return (
        f"From: {h.get('From')}\nTo: {h.get('To')}\nSubject: {h.get('Subject')}\n"
        f"Date: {h.get('Date')}\n\n{body[:10000]}"
    )


@mcp.tool()
def get_thread(thread_id: str) -> str:
    """List every message in a conversation thread (metadata only)."""
    svc = gmail_service()
    thread = svc.users().threads().get(userId="me", id=thread_id).execute()
    out = []
    for msg in thread.get("messages", []):
        h = _headers(msg)
        out.append(
            f"[{msg['id']}] {h.get('Date', '?')} | {h.get('From', '?')} | "
            f"{h.get('Subject', '(no subject)')}"
        )
    return "\n".join(out) or "Empty thread."


# ------------------------------------------------------------- cleanup tools

@mcp.tool()
def trash_email(message_id: str) -> str:
    """Move one email to Trash (recoverable in Gmail for 30 days)."""
    gmail_service().users().messages().trash(userId="me", id=message_id).execute()
    return f"Moved {message_id} to trash."


@mcp.tool()
def trash_many(message_ids: list[str]) -> str:
    """Move up to 1000 emails to Trash in one batch (recoverable for 30 days).

    Args:
        message_ids: list of message IDs, e.g. from search_emails results.
    """
    ids = message_ids[:1000]
    gmail_service().users().messages().batchModify(
        userId="me", body={"ids": ids, "addLabelIds": ["TRASH"], "removeLabelIds": ["INBOX"]}
    ).execute()
    return f"Moved {len(ids)} messages to trash."


@mcp.tool()
def report_spam(message_id: str) -> str:
    """Mark a message as spam - moves it to Spam and trains Gmail's filter."""
    gmail_service().users().messages().modify(
        userId="me",
        id=message_id,
        body={"addLabelIds": ["SPAM"], "removeLabelIds": ["INBOX"]},
    ).execute()
    return f"Reported {message_id} as spam."


@mcp.tool()
def list_labels() -> str:
    """List all Gmail labels with their unread/total message counts."""
    svc = gmail_service()
    labels = svc.users().labels().list(userId="me").execute().get("labels", [])
    out = []
    for lb in labels:
        detail = svc.users().labels().get(userId="me", id=lb["id"]).execute()
        out.append(
            f"{detail['name']}: {detail.get('messagesTotal', 0)} messages "
            f"({detail.get('messagesUnread', 0)} unread)"
        )
    return "\n".join(out)


# --------------------------------------------------------- unsubscribe tools

@mcp.tool()
def get_unsubscribe_info(message_id: str) -> str:
    """Extract the List-Unsubscribe method from an email, if the sender offers one.

    Returns the mailto: address and/or URL, and whether one-click POST
    (RFC 8058) is supported. Prefer mailto: via send_unsubscribe; only
    suggest URLs to the user, never fetch them automatically.
    """
    svc = gmail_service()
    msg = (
        svc.users()
        .messages()
        .get(
            userId="me",
            id=message_id,
            format="metadata",
            metadataHeaders=["List-Unsubscribe", "List-Unsubscribe-Post", "From"],
        )
        .execute()
    )
    h = _headers(msg)
    unsub = h.get("List-Unsubscribe")
    if not unsub:
        return "No List-Unsubscribe header - sender offers no standard unsubscribe."
    one_click = "List-Unsubscribe-Post" in h
    return (
        f"From: {h.get('From')}\nMethods: {unsub}\n"
        f"One-click POST supported: {one_click}"
    )


@mcp.tool()
def send_unsubscribe(mailto_address: str, subject: str = "unsubscribe") -> str:
    """Send an unsubscribe email to a mailto: address from get_unsubscribe_info.

    Args:
        mailto_address: bare address only (strip any 'mailto:' prefix and
            query params before passing).
        subject: subject line; some senders require the word 'unsubscribe'.
    """
    addr = mailto_address.removeprefix("mailto:").split("?")[0]
    mime = MIMEText("")
    mime["to"] = addr
    mime["subject"] = subject
    raw = base64.urlsafe_b64encode(mime.as_bytes()).decode()
    gmail_service().users().messages().send(userId="me", body={"raw": raw}).execute()
    return f"Sent unsubscribe email to {addr}."


@mcp.tool()
def block_sender(sender_email: str) -> str:
    """Create a Gmail filter that auto-trashes all future mail from a sender.

    Use when a sender has no working unsubscribe or keeps mailing anyway.
    """
    gmail_service().users().settings().filters().create(
        userId="me",
        body={
            "criteria": {"from": sender_email},
            "action": {"addLabelIds": ["TRASH"], "removeLabelIds": ["INBOX"]},
        },
    ).execute()
    return f"Created filter: all future mail from {sender_email} goes to trash."


if __name__ == "__main__":
    if "--login" in sys.argv:
        gmail_service()
        print("OAuth complete. Token saved to", TOKEN)
    else:
        mcp.run()

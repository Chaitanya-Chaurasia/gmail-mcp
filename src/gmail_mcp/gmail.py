"""Thin Gmail API wrapper returning pydantic models.

All Gmail REST plumbing lives here; tools stay one-call thin.
"""

import base64
from email.mime.text import MIMEText

from gmail_mcp.auth import gmail_service
from gmail_mcp.config import settings
from gmail_mcp.models import EmailDetail, EmailSummary, LabelInfo, SearchResult, UnsubscribeInfo

_META_HEADERS = ["From", "To", "Subject", "Date"]


def _headers(msg: dict) -> dict[str, str]:
    return {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}


def _summary(msg: dict) -> EmailSummary:
    h = _headers(msg)
    return EmailSummary(
        id=msg["id"],
        thread_id=msg.get("threadId", msg["id"]),
        date=h.get("Date", "?"),
        sender=h.get("From", "?"),
        subject=h.get("Subject", "(no subject)"),
    )


def _fetch_metadata(svc, message_id: str, extra_headers: list[str] | None = None) -> dict:
    return (
        svc.users()
        .messages()
        .get(
            userId="me",
            id=message_id,
            format="metadata",
            metadataHeaders=_META_HEADERS + (extra_headers or []),
        )
        .execute()
    )


def search(query: str, max_results: int) -> SearchResult:
    svc = gmail_service()
    max_results = max(1, min(max_results, settings.max_results_cap))
    resp = svc.users().messages().list(userId="me", q=query, maxResults=max_results).execute()
    summaries = [_fetch_metadata(svc, m["id"]) for m in resp.get("messages", [])]
    return SearchResult(
        messages=[_summary(m) for m in summaries],
        total_estimate=resp.get("resultSizeEstimate", 0),
    )


def _extract_text(part: dict) -> str:
    if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
        return base64.urlsafe_b64decode(part["body"]["data"]).decode(errors="replace")
    return "".join(_extract_text(p) for p in part.get("parts", []))


def read(message_id: str) -> EmailDetail:
    svc = gmail_service()
    msg = svc.users().messages().get(userId="me", id=message_id, format="full").execute()
    h = _headers(msg)
    return EmailDetail(
        id=msg["id"],
        sender=h.get("From", "?"),
        to=h.get("To", "?"),
        date=h.get("Date", "?"),
        subject=h.get("Subject", "(no subject)"),
        body=_extract_text(msg["payload"]) or "(no plain-text body)",
    )


def thread(thread_id: str) -> list[EmailSummary]:
    svc = gmail_service()
    t = svc.users().threads().get(userId="me", id=thread_id).execute()
    return [_summary(m) for m in t.get("messages", [])]


def trash(message_id: str) -> None:
    gmail_service().users().messages().trash(userId="me", id=message_id).execute()


def trash_batch(message_ids: list[str]) -> int:
    ids = message_ids[:1000]
    gmail_service().users().messages().batchModify(
        userId="me",
        body={"ids": ids, "addLabelIds": ["TRASH"], "removeLabelIds": ["INBOX"]},
    ).execute()
    return len(ids)


def mark_spam(message_id: str) -> None:
    gmail_service().users().messages().modify(
        userId="me",
        id=message_id,
        body={"addLabelIds": ["SPAM"], "removeLabelIds": ["INBOX"]},
    ).execute()


def labels() -> list[LabelInfo]:
    svc = gmail_service()
    out = []
    for lb in svc.users().labels().list(userId="me").execute().get("labels", []):
        detail = svc.users().labels().get(userId="me", id=lb["id"]).execute()
        out.append(
            LabelInfo(
                name=detail["name"],
                total=detail.get("messagesTotal", 0),
                unread=detail.get("messagesUnread", 0),
            )
        )
    return out


def unsubscribe_info(message_id: str) -> UnsubscribeInfo:
    svc = gmail_service()
    msg = _fetch_metadata(svc, message_id, ["List-Unsubscribe", "List-Unsubscribe-Post"])
    h = _headers(msg)
    raw = h.get("List-Unsubscribe", "")
    mailto = url = None
    for entry in raw.split(","):
        entry = entry.strip().strip("<>")
        if entry.startswith("mailto:"):
            mailto = entry.removeprefix("mailto:").split("?")[0]
        elif entry.startswith("http"):
            url = entry
    return UnsubscribeInfo(
        sender=h.get("From", "?"),
        mailto=mailto,
        url=url,
        one_click_post="List-Unsubscribe-Post" in h,
    )


def send_message(to: str, subject: str, body: str = "") -> None:
    mime = MIMEText(body)
    mime["to"] = to
    mime["subject"] = subject
    raw = base64.urlsafe_b64encode(mime.as_bytes()).decode()
    gmail_service().users().messages().send(userId="me", body={"raw": raw}).execute()


def create_block_filter(sender_email: str) -> None:
    gmail_service().users().settings().filters().create(
        userId="me",
        body={
            "criteria": {"from": sender_email},
            "action": {"addLabelIds": ["TRASH"], "removeLabelIds": ["INBOX"]},
        },
    ).execute()

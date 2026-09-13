"""Pydantic models for Gmail payloads and tool outputs.

Each model knows how to render itself as compact text - what the tools
return to the model. Every character returned lands in the LLM's context,
so renderings favor density over completeness.
"""

from pydantic import BaseModel


class EmailSummary(BaseModel):
    id: str
    thread_id: str
    date: str = "?"
    sender: str = "?"
    subject: str = "(no subject)"

    def render(self) -> str:
        return f"[{self.id}] {self.date} | {self.sender} | {self.subject}"


class SearchResult(BaseModel):
    messages: list[EmailSummary]
    total_estimate: int = 0

    def render(self) -> str:
        if not self.messages:
            return "No messages found."
        lines = [m.render() for m in self.messages]
        lines.append(f"(estimated total matches: {self.total_estimate})")
        return "\n".join(lines)


class EmailDetail(BaseModel):
    id: str
    sender: str = "?"
    to: str = "?"
    date: str = "?"
    subject: str = "(no subject)"
    body: str = "(no plain-text body)"

    def render(self, char_limit: int) -> str:
        return (
            f"From: {self.sender}\nTo: {self.to}\nSubject: {self.subject}\n"
            f"Date: {self.date}\n\n{self.body[:char_limit]}"
        )


class UnsubscribeInfo(BaseModel):
    sender: str = "?"
    mailto: str | None = None
    url: str | None = None
    one_click_post: bool = False

    def render(self) -> str:
        if not self.mailto and not self.url:
            return "No List-Unsubscribe header - sender offers no standard unsubscribe."
        lines = [f"From: {self.sender}"]
        if self.mailto:
            lines.append(f"mailto: {self.mailto} (use send_unsubscribe)")
        if self.url:
            note = (
                "one-click POST supported" if self.one_click_post else "show to user, do not fetch"
            )
            lines.append(f"url: {self.url} ({note})")
        return "\n".join(lines)


class LabelInfo(BaseModel):
    name: str
    total: int = 0
    unread: int = 0

    def render(self) -> str:
        return f"{self.name}: {self.total} messages ({self.unread} unread)"

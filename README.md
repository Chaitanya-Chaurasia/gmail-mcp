# gmail-mcp

A personal Gmail inbox-cleanup toolkit with three faces sharing one tool core:

1. **MCP server** (`src/gmail_mcp/`) - plug the tools into Claude Code
2. **Chat backend** (`backend/`) - FastAPI + Anthropic agentic loop over the
   same tools, streamed as SSE
3. **Chat frontend** (`frontend/`) - Next.js, chat-only, black & white,
   iMessage-style bubbles with timestamps, live thinking + tool-call display

## Layout

```
backend/main.py     FastAPI /api/chat - Anthropic tool loop, SSE streaming
frontend/           Next.js chat UI (shadcn-style components, Tailwind v4)
src/gmail_mcp/
  app.py            shared FastMCP instance
  config.py         pydantic-settings (.env, GMAIL_MCP_* vars)
  auth.py           OAuth flow + cached Gmail service
  gmail.py          Gmail API wrapper -> pydantic models
  models.py         EmailSummary / EmailDetail / UnsubscribeInfo / ...
  server.py         entry point (gmail-mcp / gmail-mcp --login)
  tools/
    read.py         search_emails, read_email, get_thread, list_labels
    cleanup.py      trash_email, trash_many, report_spam
    unsubscribe.py  get_unsubscribe_info, send_unsubscribe, block_sender
```

Tools stay one-call thin; Gmail REST plumbing lives in `gmail.py`; models own
their compact text rendering (everything a tool returns is LLM context).

## Tools

| Tool | Scope | What it does |
|---|---|---|
| `search_emails` | read | Gmail query search, compact results with message IDs |
| `read_email` | read | Full plain-text body of one message |
| `get_thread` | read | All messages in a conversation |
| `list_labels` | read | Labels with unread/total counts |
| `trash_email` | modify | Move one message to Trash (30-day recoverable) |
| `trash_many` | modify | Batch-trash up to 1000 IDs |
| `report_spam` | modify | Mark as spam, trains Gmail's filter |
| `get_unsubscribe_info` | read | Extract List-Unsubscribe header (RFC 2369/8058) |
| `send_unsubscribe` | send | Email a mailto: unsubscribe address |
| `block_sender` | settings | Filter that auto-trashes a sender forever |

Deliberately absent: permanent delete (requires the full `mail.google.com`
scope and is irreversible - trash is the safe ceiling for an AI agent).

## Setup

1. **Google Cloud** ([console.cloud.google.com](https://console.cloud.google.com)):
   create a project, enable the **Gmail API**, create an **OAuth client ID**
   of type **Desktop app**, download it as `credentials.json` into this
   directory (or point `GMAIL_MCP_CREDENTIALS_PATH` at it - see
   `.env.example`). Add yourself as a test user on the consent screen.

2. **Install** (uv manages the venv):
   ```sh
   uv sync
   ```

3. **One-time OAuth login** (opens a browser; token cached at
   `~/.gmail-mcp-token.json`):
   ```sh
   uv run gmail-mcp --login
   ```

4. **Register with Claude Code:**
   ```sh
   claude mcp add gmail -- uv run --directory /Users/chait/Desktop/gmail-mcp gmail-mcp
   ```
   Restart the Claude Code session; tools appear as `mcp__gmail__*`.

## Chat UI (frontend + backend)

1. Put your Anthropic key in `.env` (repo root): `ANTHROPIC_API_KEY=sk-ant-...`
2. Backend (terminal 1):
   ```sh
   uv sync --extra web
   uv run uvicorn backend.main:app --port 8000
   ```
3. Frontend (terminal 2):
   ```sh
   cd frontend && npm install && npm run dev
   ```
4. Open http://localhost:3000 and chat: the UI streams the model's summarized
   thinking, every tool call (tap to expand input/output), and the reply as
   iMessage-style bubbles. `/api/*` is proxied to the backend by Next.

## Development

```sh
uv run ruff check .        # lint
uv run ruff format .       # format
uv run mcp dev src/gmail_mcp/server.py   # MCP Inspector - call tools by hand
```

Log to stderr only - stdout carries the MCP protocol.

## Gotchas

- **Changed scopes?** Delete `~/.gmail-mcp-token.json` and re-run `--login`;
  cached tokens keep their original grants and cause 403s otherwise.
- **Unsubscribe URLs:** only mailto: addresses are acted on automatically.
  Bare URLs are returned for the human - blindly fetching unsubscribe links
  from spam confirms your address is live.
- Emails are untrusted input to the model; write-capable tools are kept
  separate so Claude Code can permission-gate them individually.

## Example cleanup session

> "Find promotional emails older than 6 months, show me the senders with the
> most mail, unsubscribe from the ones with a mailto: option, and trash all
> their old messages."

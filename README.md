# gmail-mcp

A personal Gmail MCP server for inbox cleanup, built with the official Python
MCP SDK (FastMCP). Exposes search/read/trash/spam/unsubscribe tools to Claude
Code so you can clean your inbox conversationally.

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
   directory. Add yourself as a test user on the OAuth consent screen.

2. **Install deps:**
   ```sh
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **One-time OAuth login** (opens a browser; token is cached at
   `~/.gmail-mcp-token.json`):
   ```sh
   python gmail_mcp.py --login
   ```

4. **Register with Claude Code:**
   ```sh
   claude mcp add gmail -- /Users/chait/Desktop/gmail-mcp/.venv/bin/python /Users/chait/Desktop/gmail-mcp/gmail_mcp.py
   ```
   Restart the Claude Code session; tools appear as `mcp__gmail__*`.

## Debugging

```sh
mcp dev gmail_mcp.py   # MCP Inspector - call tools by hand in a browser UI
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

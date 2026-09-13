# gmail-mcp

cleaning up my gmail with an agent. the gmail api gets wrapped into 10 tools —
search, read, trash, report spam, parse List-Unsubscribe headers, fire off
mailto: unsubscribes, block senders with filters. those tools are exposed two
ways from one core: as an mcp server that plugs straight into claude code, and
through a fastapi backend where claude-opus-5 runs an agentic loop over them,
streaming its thinking and tool calls as sse. next.js frontend renders it all
as a black & white imessage-style chat — bubbles, timestamps, collapsible
thinking and tool-call blocks. no permanent delete on purpose: trash is the
ceiling an agent gets.

## run it

```sh
# once: credentials.json from google cloud (gmail api, desktop oauth client)
uv sync --extra web
uv run gmail-mcp --login                          # one-time oauth
echo 'ANTHROPIC_API_KEY=sk-ant-...' > .env

uv run uvicorn backend.main:app --port 8000       # terminal 1
cd frontend && npm install && npm run dev         # terminal 2 → localhost:3000
```

or just the mcp server for claude code:

```sh
claude mcp add gmail -- uv run --directory . gmail-mcp
```

changed scopes? delete `~/.gmail-mcp-token.json` and re-login.

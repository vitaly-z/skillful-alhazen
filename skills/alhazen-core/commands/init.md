---
description: Start TypeDB + dashboard via Docker and load the Alhazen base schema (idempotent)
---

Initialize the Alhazen Core infrastructure. Run the command below and report the JSON result to the user:

```bash
uv run --project "${CLAUDE_PLUGIN_ROOT}" python "${CLAUDE_PLUGIN_ROOT}/alhazen_core.py" init
```

Then summarize:
- TypeDB at `localhost:1729` and dashboard at `http://localhost:3001` status
- whether the base schema (`alhazen_notebook.tql`) loaded

It is idempotent — safe to re-run. If Docker is not running, tell the user to start Docker Desktop (macOS) or `sudo systemctl start docker` (Linux) and retry.

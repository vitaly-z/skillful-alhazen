---
description: Check the Alhazen Core TypeDB + dashboard container state
---

Report the Alhazen Core infrastructure status. Run the command below and summarize the JSON for the user (Docker, TypeDB container + reachability, database existence, dashboard container + URL):

```bash
uv run --project "${CLAUDE_PLUGIN_ROOT}" python "${CLAUDE_PLUGIN_ROOT}/alhazen_core.py" status
```

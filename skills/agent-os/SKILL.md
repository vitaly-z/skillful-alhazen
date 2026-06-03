# agent-os -- Operator Context Skill

Builds a large-scale structured personal context dataset in TypeDB from connected services, with minimal operator effort. The `aos-operator-profile` role (borne by `alh-person` via `alh-role-bearing`) is the hub all context links through.

## Quick Start

```bash
# Create profile (idempotent)
uv run python skills/agent-os/agent_os.py create-profile --person op-f25ab4b15b0f

# Add context manually
uv run python skills/agent-os/agent_os.py add-goal \
  --person op-f25ab4b15b0f \
  --description "Launch product X" --priority 1

uv run python skills/agent-os/agent_os.py add-preference \
  --person op-f25ab4b15b0f \
  --category technical --description "Prefer TypeDB over SQL" --strength hard

uv run python skills/agent-os/agent_os.py add-life-event \
  --person op-f25ab4b15b0f \
  --type job-start --date 2020-01-15T00:00:00 --description "Joined CZI"

uv run python skills/agent-os/agent_os.py add-topic \
  --person op-f25ab4b15b0f \
  --name "Knowledge Graphs" --importance high

# Retrieve context
uv run python skills/agent-os/agent_os.py get-context \
  --person op-f25ab4b15b0f --dimension all

uv run python skills/agent-os/agent_os.py show-profile --person op-f25ab4b15b0f
uv run python skills/agent-os/agent_os.py show-ingestion --person op-f25ab4b15b0f
```

## Schema (`aos-` namespace)

| Type | Kind | Purpose |
|---|---|---|
| `aos-operator-profile` | `sub alh-role` | Hub role, borne by `alh-person` |
| `aos-goal` | `sub alh-domain-thing` | Goal with priority, status, deadline |
| `aos-preference` | `sub alh-domain-thing` | Work-style or technical constraint |
| `aos-life-event` | `sub alh-domain-thing` | Career/personal milestone |
| `aos-topic` | `sub alh-domain-thing` | Subject area or expertise theme |
| `aos-health-snapshot` | `sub alh-domain-thing` | Health metric reading |
| `aos-email-thread` | `sub alh-interaction` | Gmail thread |
| `aos-calendar-event` | `sub alh-interaction` | Google Calendar event |
| `aos-linkedin-message-thread` | `sub alh-interaction` | LinkedIn message thread |
| `aos-github-artifact` | `sub alh-artifact` | GitHub commit/PR/repo snapshot |
| `aos-linkedin-artifact` | `sub alh-artifact` | LinkedIn page scrape |
| `aos-healthkit-artifact` | `sub alh-artifact` | HealthKit export record |
| `aos-drive-artifact` | `sub alh-artifact` | Google Drive document |
| `aos-ingestion-note` | `sub alh-note` | Ingestion run record |

## Integration

- **`agentic-memory`**: `aos-operator-profile` coexists with `nbmem-operator-role` on same `alh-person`. Will supersede it in Phase 2.
- **`jobhunt`**: Skills bridged via `aos-skill-topic-bridge` relation (Plan 5).
- **`CLAUDE.md`**: Call `get-context --dimension all` at session start.

## Roadmap

- **Plan 2**: Gmail, Calendar, LinkedIn message adapters
- **Plan 3**: LinkedIn profile (Playwright) + GitHub adapters
- **Plan 4**: HealthKit + Drive adapters
- **Plan 5**: Bridges to agentic-memory, jobhunt, scilit, coach

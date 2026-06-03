# agent-os: Large-Scale Operator Context Skill

## Context

The operator's personal context is currently split across two siloed skills:

- **`agentic-memory`** — an `nbmem-operator-role` with 6 prose text-blob attributes (identity, role, communication style, goals, preferences, domain expertise). Currently mostly empty.
- **`jobhunt`** — 26 `jhunt-your-skill` entities with structured Bloom's-level proficiency, evidence, and recency. Well-populated but scoped to job search.

Neither system ingests data from external sources. The "personal context portfolio" concept (10 structured dimensions of who the operator is, how they work, and what they're doing) is largely unrealised.

`agent-os` is a new core skill that builds a **large-scale, structured operator context dataset** from connected services (Gmail, Google Calendar, GitHub, LinkedIn, Google Drive, HealthKit), with minimal operator effort. It uses TypeDB as the single source of truth, following the established Alhazen schema hierarchy (`domain-thing` / `artifact` / `note`), and starts as a bridge over existing skills with a clear migration path toward becoming the authoritative context hub.

## Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| New skill vs. extend agentic-memory | New skill: `agent-os` | Different responsibility — ingestion pipeline vs. episodic memory |
| Skill name | `agent-os` | Reflects role as the operator context layer of the Agent OS |
| Data sources | Gmail, Calendar, GitHub, LinkedIn (Playwright), Google Drive, HealthKit | Full life-OS scope: work + code + career + relationships + health |
| Ingestion model | On-demand (user triggers sync) | Full user control; automation can be layered later |
| Context representation | Tiered hybrid: core entities + structured attributes + on-demand prose | Schema is rigorous and queryable; prose synthesis done by agent as needed |
| Schema base types | Use Alhazen hierarchy: `domain-thing`, `artifact`, `note`, `alh-interaction` | No novel patterns; inherits all existing attributes and relations |
| LinkedIn ingestion | Playwright browser scraping (user logs in manually) | No API available; scraping own data is acceptable; avoids 24hr export wait |
| LinkedIn messages | Scraped as `aos-linkedin-message-thread sub alh-interaction` | Significant professional communication channel |
| Prose summaries | Not pre-stored; generated on demand by agent from structured data | Schema is the source of truth; no stale summary problem |
| Relationship to existing skills | Bridge + extend (gradual migration) | Nothing breaks today; schema designed with hub destination in mind |
| Other communication channels | Gmail + LinkedIn messages only (Slack, iMessage deferred) | Covers meaningful professional channels; extend later if needed |

## Schema (`aos-` namespace)

### Role (hub)

```
aos-operator-profile sub alh-role
  owns aos-timezone
  owns aos-location-preference
  owns aos-target-role
```

Borne by `alh-person` via `alh-role-bearing`, same pattern as `nbmem-operator-role` and `jhunt-job-seeker-role`. This becomes the hub all context links through.

### Domain-Things (real-world objects, not content)

```
aos-topic sub alh-domain-thing
  owns aos-importance         # high | medium | low
  owns aos-last-active        # datetime
  # canonical label uses inherited `name`; description uses inherited `description`

aos-goal sub alh-domain-thing
  owns aos-priority           # integer 1-5
  owns aos-goal-status        # active | completed | dropped
  owns aos-target-date        # datetime (optional)
  # description inherited from alh-identifiable-entity

aos-preference sub alh-domain-thing
  owns aos-preference-category  # work-style | technical | communication | personal
  owns aos-preference-strength  # hard | soft
  # description inherited

aos-life-event sub alh-domain-thing
  owns aos-event-type         # job-start | job-end | publication | conference | project-launch | education-start | education-end | award
  owns aos-event-date         # datetime
  # description, name inherited

aos-health-snapshot sub alh-domain-thing
  owns aos-metric-type        # steps | sleep-hours | hrv | active-calories | weight | resting-hr
  owns aos-metric-value       # double
  owns aos-metric-unit        # string e.g. "steps", "hours", "ms"
  owns aos-metric-date        # date
  owns aos-metric-source      # healthkit | manual
```

### Interactions (sub alh-interaction, which is sub alh-domain-thing)

`alh-interaction` already owns `alh-interaction-type`, `alh-interaction-date`, `alh-outcome`, `alh-follow-up-by`, `alh-follow-up-status` and plays `alh-interaction-participation`. These subtypes add source-specific identifiers:

```
aos-email-thread sub alh-interaction
  owns aos-gmail-thread-id    # Gmail thread ID for deduplication
  owns aos-subject
  owns aos-message-count

aos-calendar-event sub alh-interaction
  owns aos-calendar-event-id  # Google Calendar event ID
  owns aos-duration-minutes
  owns aos-recurrence         # none | daily | weekly | monthly

aos-linkedin-message-thread sub alh-interaction
  owns aos-linkedin-thread-id
  owns aos-message-count
```

### Artifacts (raw ingested content, sub alh-artifact)

```
aos-github-artifact sub alh-artifact
  owns aos-github-repo        # "owner/repo"
  owns aos-github-event-type  # commit | pr | release | repo-created

aos-linkedin-artifact sub alh-artifact
  owns aos-linkedin-page      # URL of scraped page

aos-healthkit-artifact sub alh-artifact
  owns aos-healthkit-export-date

aos-drive-artifact sub alh-artifact
  owns aos-drive-file-id
  owns aos-drive-mime-type
```

### Notes (agent-generated, sub alh-note)

```
aos-ingestion-note sub alh-note
  owns aos-ingestion-source   # gmail | calendar | github | linkedin | healthkit | drive
  owns aos-items-processed    # integer
  owns aos-watermark          # datetime — last item ingested, for delta sync
```

Ingestion notes are linked to `aos-operator-profile` via `alh-aboutness`.

### Relations

```
aos-profile-has-goal
  relates profile (aos-operator-profile)
  relates goal (aos-goal)

aos-profile-has-preference
  relates profile (aos-operator-profile)
  relates preference (aos-preference)

aos-profile-has-life-event
  relates profile (aos-operator-profile)
  relates event (aos-life-event)

aos-interaction-about
  relates interaction (alh-interaction)
  relates topic (aos-topic)

aos-topic-evidenced-by
  relates topic (aos-topic)
  relates evidence (alh-identifiable-entity)  # interaction, artifact, episode, publication

aos-skill-topic-bridge
  relates skill (jhunt-your-skill)
  relates topic (aos-topic)
  # same real-world concept across skills
```

`alh-interaction-participation` (core) handles linking interactions to `alh-person` participants — no new relation needed.

## Source Adapters

Each adapter is a focused Python module. All produce the same three outputs: typed domain-thing entities, raw artifacts, and an `aos-ingestion-note`.

### Gmail (`sync gmail`)
- **Tool**: existing Gmail MCP (`search_threads`, `get_thread`)
- **Produces**: `aos-email-thread` per thread, `alh-person` per participant, `aos-topic` links (LLM topic tagging from subject/body — the only LLM-in-ingestion step)
- **Deduplication**: `aos-gmail-thread-id` prevents re-ingesting known threads

### Google Calendar (`sync calendar`)
- **Tool**: existing Calendar MCP (`list_events`)
- **Produces**: `aos-calendar-event` per event, `alh-person` per attendee
- **Deduplication**: `aos-calendar-event-id`

### GitHub (`sync github`)
- **Tool**: `gh api` CLI (already available)
- **Produces**: `aos-github-artifact` per significant activity, `aos-life-event` for milestones (repo creation, major release), `aos-topic` evidence from repo languages and topics → bridged to `jhunt-your-skill` via `aos-skill-topic-bridge`
- **No LLM needed**: structured API data throughout

### LinkedIn (`sync linkedin`)
- **Tool**: Playwright MCP (`mcp__playwright__*`) — user logs into LinkedIn manually first
- **Pages scraped**:

  | Page | Entities produced |
  |---|---|
  | `/in/{username}` | Headline → updates `aos-operator-profile` |
  | `/in/{username}/details/experience/` | `aos-life-event` (job-start/job-end) + `alh-organization` per employer |
  | `/in/{username}/details/education/` | `aos-life-event` (education-start/end) |
  | `/in/{username}/details/skills/` | Evidence to enrich `jhunt-your-skill` + `aos-topic` |
  | `/in/{username}/details/publications/` | `aos-life-event` (publication); cross-references DOI to `scilit` artifacts |
  | `/mynetwork/invite-connect/connections/` | `alh-person` per connection |
  | `/messaging/` + thread pages | `aos-linkedin-message-thread` per conversation + `alh-person` participants |

- **Raw content**: `aos-linkedin-artifact` per page (full DOM stored in `cache-path`)
- **Deduplication**: page URL + scrape date; re-runs diff against previous `aos-linkedin-artifact`

### Google Drive (`sync drive`)
- **Tool**: existing Drive MCP (`list_recent_files`, `read_file_content`)
- **Produces**: `aos-drive-artifact` per document, `aos-topic` links from titles/descriptions
- **Deduplication**: `aos-drive-file-id`

### HealthKit (`sync healthkit`)
- **Tool**: XML export from Apple Health app (user provides file path)
- **Produces**: `aos-health-snapshot` per metric type per day, `aos-healthkit-artifact` per batch
- **Note**: coach skill owns health goal tracking and appointments; `agent-os` owns raw metrics only

## CLI Interface

```bash
# Ingestion
agent-os sync gmail      [--days 30]
agent-os sync calendar   [--days 30]
agent-os sync github     [--username gulzarooster]
agent-os sync linkedin   [--profile-url URL]   # requires Playwright + user logged in
agent-os sync healthkit  [--export ~/health.xml]
agent-os sync drive      [--days 30]
agent-os sync all        [--days 30]

# Manual entry (for things no adapter captures)
agent-os add-goal       --description "..." --priority 3 [--target-date 2026-12-31]
agent-os add-preference --category technical --description "..." --strength hard
agent-os add-life-event --type job-start --date 2020-01-01 --org "CZI" --description "..."
agent-os add-topic      --label "..." --description "..." --importance high

# Context retrieval
agent-os get-context    [--dimension expertise|goals|preferences|relationships|career|health|all]
agent-os show-profile   # full structured profile, all dimensions
agent-os show-ingestion # last sync timestamps per source + item counts
```

`get-context` returns structured JSON (Tier 1+2 graph data). Prose synthesis is done by the calling agent on demand — no pre-baked summary stored.

## Integration with Existing Skills

**`agentic-memory`**: `aos-operator-profile` will supersede `nbmem-operator-role` as the context hub over time. During migration, both roles coexist on the same `alh-person`; `get-context` falls back to `nbmem-operator-role` if no `aos-operator-profile` exists. Memory claims and episodes are unaffected — they link to `alh-identifiable-entity`, which `aos-operator-profile` satisfies.

**`jobhunt`**: `jhunt-your-skill` entities bridged to `aos-topic` via `aos-skill-topic-bridge`. GitHub sync enriches skill evidence when relevant repos are found. Gap analysis (`show-gaps`) unchanged.

**`scientific-literature`**: Publications from LinkedIn and GitHub cross-referenced to existing `scilit` artifacts by DOI. `aos-life-event` (type: publication) links to the `alh-artifact` already in the graph.

**`coach`**: `agent-os` ingests raw health metrics into `aos-health-snapshot`; coach retains ownership of health goals and appointments. Both skills share the same TypeDB database.

**`CLAUDE.md` coordinator**: `agent-os get-context --dimension all` replaces (or supplements) `agentic-memory get-context` at session start.

## Migration Path (bridge → hub)

1. **Phase 1 (this spec)**: `agent-os` as bridge — owns new entity types, bridges to existing skills via `aos-skill-topic-bridge` and entity aliases
2. **Phase 2**: `nbmem-operator-role` absorbed into `aos-operator-profile`; `agentic-memory` retains only episodic/claim functionality
3. **Phase 3**: `jhunt-your-skill` migrated to `aos-topic` subtypes; `jobhunt` becomes a search/application tracking skill, not a skills registry

Each phase is independent and non-breaking.

## Out of Scope

- Background/scheduled ingestion (defer; on-demand is Phase 1)
- Slack, iMessage, or other communication channels (extend later)
- LLM-driven entity extraction beyond Gmail topic tagging
- Dashboard UI (separate skill dashboard work)
- Multi-operator support (single operator assumed)

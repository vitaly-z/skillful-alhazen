# agent-os Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the `agent-os` skill foundation: TypeDB schema (`aos-` namespace), core CLI with operator profile CRUD, manual entry commands (add-goal, add-preference, add-life-event, add-topic), and context retrieval (get-context, show-profile, show-ingestion).

**Architecture:** New skill in `skills/agent-os/` following the exact same patterns as `agentic-memory` — TypeDB connection via environment variables, argparse CLI, JSON stdout output. The `aos-operator-profile` role (sub `alh-role`) is the context hub, borne by `alh-person` via `alh-role-bearing`. Goals, preferences, life-events, and topics are `sub alh-domain-thing` linked to the profile via typed relations.

**Tech Stack:** Python 3.11+, typedb-driver>=3.8.0, TypeDB 3.8.0, argparse, uv

---

> **This is Plan 1 of 5.** Subsequent plans: (2) Communication adapters — Gmail, Calendar, LinkedIn messages; (3) Career/code adapters — LinkedIn profile (Playwright), GitHub; (4) Life/health adapters — HealthKit, Google Drive; (5) Skill integration — bridges to agentic-memory, jobhunt, scilit.

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `skills/agent-os/schema.tql` | Create | Full `aos-` namespace TypeDB schema |
| `skills/agent-os/agent_os.py` | Create | CLI — all commands, TypeDB queries |
| `skills/agent-os/skill.yaml` | Create | Skill metadata and registry entry |
| `skills/agent-os/SKILL.md` | Create | Usage documentation |
| `skills-registry.yaml` | Modify | Register `agent-os` skill |
| `tests/test_agent_os.py` | Create | Integration tests against live TypeDB |

---

## Task 1: Schema and Skill Scaffold

**Files:**
- Create: `skills/agent-os/schema.tql`
- Create: `skills/agent-os/skill.yaml`

- [ ] **Step 1: Create the skill directory**

```bash
mkdir -p skills/agent-os
```

- [ ] **Step 2: Write `skills/agent-os/schema.tql`**

Write the following content exactly:

```typeql
# =============================================================================
# agent-os namespace schema
# Operator context skill: large-scale personal context dataset
# =============================================================================

# =============================================================================
# ATTRIBUTES
# =============================================================================

attribute aos-timezone, value string;
attribute aos-location-preference, value string;
attribute aos-target-role, value string;
attribute aos-importance, value string;
attribute aos-last-active, value datetime;
attribute aos-priority, value integer;
attribute aos-goal-status, value string;
attribute aos-target-date, value datetime;
attribute aos-preference-category, value string;
attribute aos-preference-strength, value string;
attribute aos-event-type, value string;
attribute aos-event-date, value datetime;
attribute aos-metric-type, value string;
attribute aos-metric-value, value double;
attribute aos-metric-unit, value string;
attribute aos-metric-date, value datetime;
attribute aos-metric-source, value string;
attribute aos-gmail-thread-id, value string;
attribute aos-subject, value string;
attribute aos-message-count, value integer;
attribute aos-calendar-event-id, value string;
attribute aos-duration-minutes, value integer;
attribute aos-recurrence, value string;
attribute aos-linkedin-thread-id, value string;
attribute aos-github-repo, value string;
attribute aos-github-event-type, value string;
attribute aos-linkedin-page, value string;
attribute aos-healthkit-export-date, value datetime;
attribute aos-drive-file-id, value string;
attribute aos-drive-mime-type, value string;
attribute aos-ingestion-source, value string;
attribute aos-items-processed, value integer;
attribute aos-watermark, value datetime;

# =============================================================================
# RELATIONS (before entities so role names resolve in plays clauses)
# =============================================================================

relation aos-profile-has-goal,
    relates profile,
    relates goal;

relation aos-profile-has-preference,
    relates profile,
    relates preference;

relation aos-profile-has-life-event,
    relates profile,
    relates event;

relation aos-interaction-about,
    relates interaction,
    relates topic;

relation aos-topic-evidenced-by,
    relates topic,
    relates evidence;

relation aos-skill-topic-bridge,
    relates skill,
    relates topic;

# =============================================================================
# ENTITIES
# =============================================================================

entity aos-operator-profile sub alh-role,
    owns aos-timezone,
    owns aos-location-preference,
    owns aos-target-role,
    plays alh-role-bearing:borne-role,
    plays alh-aboutness:subject,
    plays aos-profile-has-goal:profile,
    plays aos-profile-has-preference:profile,
    plays aos-profile-has-life-event:profile;

entity aos-topic sub alh-domain-thing,
    owns aos-importance,
    owns aos-last-active,
    plays aos-interaction-about:topic,
    plays aos-topic-evidenced-by:topic,
    plays aos-skill-topic-bridge:topic;

entity aos-goal sub alh-domain-thing,
    owns aos-priority,
    owns aos-goal-status,
    owns aos-target-date,
    plays aos-profile-has-goal:goal;

entity aos-preference sub alh-domain-thing,
    owns aos-preference-category,
    owns aos-preference-strength,
    plays aos-profile-has-preference:preference;

entity aos-life-event sub alh-domain-thing,
    owns aos-event-type,
    owns aos-event-date,
    plays aos-profile-has-life-event:event;

entity aos-health-snapshot sub alh-domain-thing,
    owns aos-metric-type,
    owns aos-metric-value,
    owns aos-metric-unit,
    owns aos-metric-date,
    owns aos-metric-source;

entity aos-email-thread sub alh-interaction,
    owns aos-gmail-thread-id,
    owns aos-subject,
    owns aos-message-count,
    plays alh-interaction-participation:alh-interaction,
    plays aos-interaction-about:interaction;

entity aos-calendar-event sub alh-interaction,
    owns aos-calendar-event-id,
    owns aos-duration-minutes,
    owns aos-recurrence,
    plays alh-interaction-participation:alh-interaction,
    plays aos-interaction-about:interaction;

entity aos-linkedin-message-thread sub alh-interaction,
    owns aos-linkedin-thread-id,
    owns aos-message-count,
    plays alh-interaction-participation:alh-interaction,
    plays aos-interaction-about:interaction;

entity aos-github-artifact sub alh-artifact,
    owns aos-github-repo,
    owns aos-github-event-type;

entity aos-linkedin-artifact sub alh-artifact,
    owns aos-linkedin-page;

entity aos-healthkit-artifact sub alh-artifact,
    owns aos-healthkit-export-date;

entity aos-drive-artifact sub alh-artifact,
    owns aos-drive-file-id,
    owns aos-drive-mime-type;

entity aos-ingestion-note sub alh-note,
    owns aos-ingestion-source,
    owns aos-items-processed,
    owns aos-watermark,
    plays alh-aboutness:note;
```

- [ ] **Step 3: Write `skills/agent-os/skill.yaml`**

```yaml
name: agent-os
version: 0.1.0
description: Large-scale operator context dataset — ingests Gmail, Calendar, GitHub, LinkedIn, Drive, and HealthKit into TypeDB for rich structured personal context.
author: skillful-alhazen
license: MIT
typedb_schema: schema.tql
cli: agent_os.py
dependencies:
  - alhazen-core
schema:
  namespace: aos
  depends_on: []
tags:
  - memory
  - agents
  - personal-context
  - knowledge-graph
  - ingestion
```

- [ ] **Step 4: Register in `skills-registry.yaml`**

Add after the `agentic-memory` entry:

```yaml
- name: agent-os
  path: skills/agent-os
```

- [ ] **Step 5: Load the schema into TypeDB**

```bash
# Step 5a: Backup first (REQUIRED — db-init is destructive)
make db-export

# Step 5b: Build skills so local_skills/agent-os/ is created
make build-skills

# Step 5c: Reload all schemas including the new agent-os schema
make db-init
```

Expected output ends with: `✓ Database initialized`

- [ ] **Step 6: Verify the schema loaded**

```bash
uv run python -c "
from typedb.driver import Credentials, DriverOptions, TransactionType, TypeDB
with TypeDB.driver('localhost:1729', Credentials('admin','password'), DriverOptions(is_tls_enabled=False)) as d:
    with d.transaction('alhazen_notebook', TransactionType.READ) as tx:
        q = 'match \$t sub aos-operator-profile; fetch { \"label\": \$t.label; };'
        r = list(tx.query(q).resolve())
        print('aos-operator-profile found:', len(r) > 0)
        q2 = 'match \$t sub aos-goal; fetch { \"label\": \$t.label; };'
        r2 = list(tx.query(q2).resolve())
        print('aos-goal found:', len(r2) > 0)
"
```

Expected:
```
aos-operator-profile found: True
aos-goal found: True
```

- [ ] **Step 7: Commit**

```bash
git add skills/agent-os/schema.tql skills/agent-os/skill.yaml skills-registry.yaml
git commit -m "feat(agent-os): add schema and skill registration"
```

---

## Task 2: CLI Boilerplate + create-profile Command

**Files:**
- Create: `skills/agent-os/agent_os.py`

- [ ] **Step 1: Write the failing test for create-profile**

```python
# tests/test_agent_os.py
"""
Tests for the agent-os skill CLI.
Requires running TypeDB with schema loaded: make db-start && make db-init
Run: pytest tests/test_agent_os.py -v
"""

import json
import os
import subprocess
import uuid

import pytest

pytest.importorskip("typedb.driver")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(PROJECT_ROOT, "skills", "agent-os", "agent_os.py")
ENV = {**os.environ, "TYPEDB_DATABASE": "alhazen_notebook"}
OPERATOR_ID = "op-f25ab4b15b0f"


def run_cmd(*args: str, expect_success: bool = True) -> dict:
    result = subprocess.run(
        ["uv", "run", "python", SCRIPT, *args],
        capture_output=True, text=True, env=ENV, cwd=PROJECT_ROOT,
    )
    assert result.stdout.strip(), f"No stdout: {args}\nstderr: {result.stderr[:500]}"
    data = json.loads(result.stdout)
    if expect_success:
        assert data.get("success") is True, f"Command failed: {data}"
    return data


def typedb_delete(query: str):
    """Run a raw TypeDB delete for test cleanup."""
    from typedb.driver import Credentials, DriverOptions, TransactionType, TypeDB
    with TypeDB.driver(
        "localhost:1729", Credentials("admin", "password"), DriverOptions(is_tls_enabled=False)
    ) as driver:
        with driver.transaction("alhazen_notebook", TransactionType.WRITE) as tx:
            tx.query(query).resolve()
            tx.commit()


class TestCreateProfile:
    def test_create_profile_for_operator(self):
        result = run_cmd("create-profile", "--person", OPERATOR_ID)
        profile_id = result["profile_id"]
        assert profile_id.startswith("aos-profile-")
        # Cleanup
        typedb_delete(
            f'match $p isa aos-operator-profile, has id "{profile_id}"; '
            f'$r (bearer: $person, borne-role: $p) isa alh-role-bearing; '
            f'delete $r; delete $p;'
        )

    def test_create_profile_idempotent(self):
        """Creating a profile when one exists should return the existing profile."""
        r1 = run_cmd("create-profile", "--person", OPERATOR_ID)
        r2 = run_cmd("create-profile", "--person", OPERATOR_ID)
        assert r1["profile_id"] == r2["profile_id"]
        # Cleanup
        typedb_delete(
            f'match $p isa aos-operator-profile, has id "{r1["profile_id"]}"; '
            f'$r (bearer: $person, borne-role: $p) isa alh-role-bearing; '
            f'delete $r; delete $p;'
        )
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
pytest tests/test_agent_os.py::TestCreateProfile -v
```

Expected: `ERROR` — `agent_os.py` not found.

- [ ] **Step 3: Write `skills/agent-os/agent_os.py` with boilerplate + create-profile**

```python
#!/usr/bin/env python3
"""
agent-os CLI — large-scale operator context dataset.

Builds a structured personal context graph in TypeDB from connected services
(Gmail, Calendar, GitHub, LinkedIn, Drive, HealthKit) and manual entry.

Usage:
    python skills/agent-os/agent_os.py <command> [options]

Profile commands:
    create-profile     Create aos-operator-profile for a person (idempotent)
    show-profile       Show full structured profile for a person
    show-ingestion     Show last ingestion timestamps per source

Manual entry commands:
    add-goal           Add a goal linked to the operator profile
    add-preference     Add a preference or constraint
    add-life-event     Add a career/personal milestone
    add-topic          Add a topic/interest area

Context retrieval:
    get-context        Get structured context JSON (all or one dimension)

Environment:
    TYPEDB_HOST       TypeDB server host (default: localhost)
    TYPEDB_PORT       TypeDB server port (default: 1729)
    TYPEDB_DATABASE   Database name (default: alhazen_notebook)
    TYPEDB_USERNAME   TypeDB username (default: admin)
    TYPEDB_PASSWORD   TypeDB password (default: password)
"""

import argparse
import json
import os
import sys

try:
    from typedb.driver import Credentials, DriverOptions, TransactionType, TypeDB
    TYPEDB_AVAILABLE = True
except ImportError:
    TYPEDB_AVAILABLE = False
    print("Warning: typedb-driver not installed. pip install 'typedb-driver>=3.8.0'", file=sys.stderr)

try:
    _SKILL_DIR = os.path.dirname(os.path.realpath(__file__))
    _PROJECT_ROOT = os.path.abspath(os.path.join(_SKILL_DIR, "..", ".."))
    sys.path.insert(0, _PROJECT_ROOT)
    from src.skillful_alhazen.utils.skill_helpers import escape_string, generate_id, get_timestamp
except ImportError:
    import uuid
    from datetime import datetime, timezone

    def escape_string(s: str) -> str:
        if s is None:
            return ""
        return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "")

    def generate_id(prefix: str) -> str:
        return f"{prefix}-{uuid.uuid4().hex[:12]}"

    def get_timestamp() -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


TYPEDB_HOST = os.getenv("TYPEDB_HOST", "localhost")
TYPEDB_PORT = int(os.getenv("TYPEDB_PORT", "1729"))
TYPEDB_DATABASE = os.getenv("TYPEDB_DATABASE", "alhazen_notebook")
TYPEDB_USERNAME = os.getenv("TYPEDB_USERNAME", "admin")
TYPEDB_PASSWORD = os.getenv("TYPEDB_PASSWORD", "password")


def get_driver():
    return TypeDB.driver(
        f"{TYPEDB_HOST}:{TYPEDB_PORT}",
        Credentials(TYPEDB_USERNAME, TYPEDB_PASSWORD),
        DriverOptions(is_tls_enabled=False),
    )


def _find_profile(driver, person_id: str) -> str | None:
    """Return the aos-operator-profile ID for a person, or None."""
    pid = escape_string(person_id)
    with driver.transaction(TYPEDB_DATABASE, TransactionType.READ) as tx:
        results = list(tx.query(f'''
            match
              $person isa alh-person, has id "{pid}";
              (bearer: $person, borne-role: $profile) isa alh-role-bearing;
              $profile isa aos-operator-profile, has id $pid;
            fetch {{ "id": $pid }};
        ''').resolve())
    if not results:
        return None
    return results[0]["id"]["value"]


def cmd_create_profile(args):
    """Create aos-operator-profile for a person (idempotent)."""
    pid = escape_string(args.person)
    ts = get_timestamp()

    with get_driver() as driver:
        existing = _find_profile(driver, args.person)
        if existing:
            print(json.dumps({"success": True, "profile_id": existing, "created": False}))
            return

        profile_id = generate_id("aos-profile")
        profile_q = f'''
        insert $profile isa aos-operator-profile,
            has id "{profile_id}",
            has name "{pid} (agent-os profile)",
            has alh-role-status "active",
            has created-at {ts};
        '''
        bearing_q = f'''
        match
          $person isa alh-person, has id "{pid}";
          $profile isa aos-operator-profile, has id "{profile_id}";
        insert (bearer: $person, borne-role: $profile) isa alh-role-bearing;
        '''

        with driver.transaction(TYPEDB_DATABASE, TransactionType.WRITE) as tx:
            tx.query(profile_q).resolve()
            tx.commit()
        with driver.transaction(TYPEDB_DATABASE, TransactionType.WRITE) as tx:
            tx.query(bearing_q).resolve()
            tx.commit()

    print(json.dumps({"success": True, "profile_id": profile_id, "created": True}))


# ---------------------------------------------------------------------------
# Argparse
# ---------------------------------------------------------------------------

def build_parser():
    parser = argparse.ArgumentParser(
        prog="agent-os",
        description="agent-os: large-scale operator context dataset",
    )
    sub = parser.add_subparsers(dest="command")

    # create-profile
    p = sub.add_parser("create-profile", help="Create aos-operator-profile for a person (idempotent)")
    p.add_argument("--person", required=True, help="alh-person ID")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    dispatch = {
        "create-profile": cmd_create_profile,
    }

    fn = dispatch.get(args.command)
    if fn is None:
        print(json.dumps({"success": False, "error": f"Unknown command: {args.command}"}))
        sys.exit(1)

    fn(args)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the test to verify it passes**

```bash
pytest tests/test_agent_os.py::TestCreateProfile -v
```

Expected:
```
tests/test_agent_os.py::TestCreateProfile::test_create_profile_for_operator PASSED
tests/test_agent_os.py::TestCreateProfile::test_create_profile_idempotent PASSED
```

- [ ] **Step 5: Commit**

```bash
git add skills/agent-os/agent_os.py tests/test_agent_os.py
git commit -m "feat(agent-os): add create-profile command with idempotency"
```

---

## Task 3: Manual Entry Commands (add-goal, add-preference, add-life-event, add-topic)

**Files:**
- Modify: `skills/agent-os/agent_os.py`
- Modify: `tests/test_agent_os.py`

- [ ] **Step 1: Write failing tests for all four commands**

Add to `tests/test_agent_os.py`:

```python
class TestManualEntry:
    """Tests for add-goal, add-preference, add-life-event, add-topic."""

    TEST_TAG = uuid.uuid4().hex[:8]  # unique per test run for cleanup

    @classmethod
    def setup_class(cls):
        """Ensure a profile exists for the operator."""
        run_cmd("create-profile", "--person", OPERATOR_ID)

    def test_add_goal(self):
        desc = f"Test goal {self.TEST_TAG}"
        result = run_cmd(
            "add-goal", "--person", OPERATOR_ID,
            "--description", desc,
            "--priority", "3",
        )
        assert result["id"].startswith("aos-goal-")
        typedb_delete(f'match $g isa aos-goal, has id "{result["id"]}"; '
                      f'$r (profile: $p, goal: $g) isa aos-profile-has-goal; '
                      f'delete $r; delete $g;')

    def test_add_goal_with_target_date(self):
        desc = f"Test goal with date {self.TEST_TAG}"
        result = run_cmd(
            "add-goal", "--person", OPERATOR_ID,
            "--description", desc,
            "--priority", "1",
            "--target-date", "2026-12-31T00:00:00",
        )
        assert result["id"].startswith("aos-goal-")
        typedb_delete(f'match $g isa aos-goal, has id "{result["id"]}"; '
                      f'$r (profile: $p, goal: $g) isa aos-profile-has-goal; '
                      f'delete $r; delete $g;')

    def test_add_preference(self):
        result = run_cmd(
            "add-preference", "--person", OPERATOR_ID,
            "--category", "technical",
            "--description", f"Prefer TypeDB {self.TEST_TAG}",
            "--strength", "hard",
        )
        assert result["id"].startswith("aos-pref-")
        typedb_delete(f'match $p isa aos-preference, has id "{result["id"]}"; '
                      f'$r (profile: $pr, preference: $p) isa aos-profile-has-preference; '
                      f'delete $r; delete $p;')

    def test_add_life_event(self):
        result = run_cmd(
            "add-life-event", "--person", OPERATOR_ID,
            "--type", "job-start",
            "--date", "2020-01-15T00:00:00",
            "--description", f"Started at CZI {self.TEST_TAG}",
        )
        assert result["id"].startswith("aos-event-")
        typedb_delete(f'match $e isa aos-life-event, has id "{result["id"]}"; '
                      f'$r (profile: $p, event: $e) isa aos-profile-has-life-event; '
                      f'delete $r; delete $e;')

    def test_add_topic(self):
        result = run_cmd(
            "add-topic", "--person", OPERATOR_ID,
            "--name", f"Test Topic {self.TEST_TAG}",
            "--description", "A test topic",
            "--importance", "high",
        )
        assert result["id"].startswith("aos-topic-")
        typedb_delete(f'match $t isa aos-topic, has id "{result["id"]}"; delete $t;')
```

- [ ] **Step 2: Run to confirm failures**

```bash
pytest tests/test_agent_os.py::TestManualEntry -v
```

Expected: All 5 tests fail with `"Unknown command"` or similar.

- [ ] **Step 3: Implement the four commands in `agent_os.py`**

Add these four functions before `build_parser()`:

```python
def cmd_add_goal(args):
    """Add an aos-goal linked to the operator's profile."""
    ts = get_timestamp()
    profile_id = _get_profile_id_or_exit(args.person)
    gid = generate_id("aos-goal")
    desc = escape_string(args.description)
    priority = args.priority

    q = f'''
    match $profile isa aos-operator-profile, has id "{escape_string(profile_id)}";
    insert
      $goal isa aos-goal,
        has id "{gid}",
        has description "{desc}",
        has aos-priority {priority},
        has aos-goal-status "active",
        has created-at {ts}'''
    if args.target_date:
        q += f',\n        has aos-target-date {escape_string(args.target_date)}'
    q += ';\n      (profile: $profile, goal: $goal) isa aos-profile-has-goal;'

    with get_driver() as driver:
        with driver.transaction(TYPEDB_DATABASE, TransactionType.WRITE) as tx:
            tx.query(q).resolve()
            tx.commit()

    print(json.dumps({"success": True, "id": gid}))


def cmd_add_preference(args):
    """Add an aos-preference linked to the operator's profile."""
    ts = get_timestamp()
    profile_id = _get_profile_id_or_exit(args.person)
    pid = generate_id("aos-pref")
    desc = escape_string(args.description)
    cat = escape_string(args.category)
    strength = escape_string(args.strength)

    q = f'''
    match $profile isa aos-operator-profile, has id "{escape_string(profile_id)}";
    insert
      $pref isa aos-preference,
        has id "{pid}",
        has description "{desc}",
        has aos-preference-category "{cat}",
        has aos-preference-strength "{strength}",
        has created-at {ts};
      (profile: $profile, preference: $pref) isa aos-profile-has-preference;
    '''

    with get_driver() as driver:
        with driver.transaction(TYPEDB_DATABASE, TransactionType.WRITE) as tx:
            tx.query(q).resolve()
            tx.commit()

    print(json.dumps({"success": True, "id": pid}))


def cmd_add_life_event(args):
    """Add an aos-life-event linked to the operator's profile."""
    ts = get_timestamp()
    profile_id = _get_profile_id_or_exit(args.person)
    eid = generate_id("aos-event")
    desc = escape_string(args.description)
    event_type = escape_string(args.type)
    event_date = escape_string(args.date)

    q = f'''
    match $profile isa aos-operator-profile, has id "{escape_string(profile_id)}";
    insert
      $event isa aos-life-event,
        has id "{eid}",
        has description "{desc}",
        has aos-event-type "{event_type}",
        has aos-event-date {event_date},
        has created-at {ts};
      (profile: $profile, event: $event) isa aos-profile-has-life-event;
    '''

    with get_driver() as driver:
        with driver.transaction(TYPEDB_DATABASE, TransactionType.WRITE) as tx:
            tx.query(q).resolve()
            tx.commit()

    print(json.dumps({"success": True, "id": eid}))


def cmd_add_topic(args):
    """Add an aos-topic (global — discovered from interactions or manually added)."""
    ts = get_timestamp()
    tid = generate_id("aos-topic")
    name = escape_string(args.name)
    desc = escape_string(args.description or "")
    importance = escape_string(args.importance)

    q = f'''
    insert $topic isa aos-topic,
        has id "{tid}",
        has name "{name}",
        has aos-importance "{importance}",
        has created-at {ts}'''
    if desc:
        q += f',\n        has description "{desc}"'
    q += ";"

    with get_driver() as driver:
        with driver.transaction(TYPEDB_DATABASE, TransactionType.WRITE) as tx:
            tx.query(q).resolve()
            tx.commit()

    print(json.dumps({"success": True, "id": tid}))


def _get_profile_id_or_exit(person_id: str) -> str:
    """Find profile ID or print error and exit."""
    with get_driver() as driver:
        profile_id = _find_profile(driver, person_id)
    if not profile_id:
        print(json.dumps({
            "success": False,
            "error": f"No aos-operator-profile found for person '{person_id}'. Run create-profile first."
        }))
        sys.exit(1)
    return profile_id
```

Also update `build_parser()` and `dispatch` dict in `main()`:

In `build_parser()`, add after the `create-profile` parser:

```python
    # add-goal
    p = sub.add_parser("add-goal", help="Add a goal linked to the operator profile")
    p.add_argument("--person", required=True)
    p.add_argument("--description", required=True)
    p.add_argument("--priority", type=int, required=True, choices=[1,2,3,4,5])
    p.add_argument("--target-date", help="ISO datetime e.g. 2026-12-31T00:00:00")

    # add-preference
    p = sub.add_parser("add-preference", help="Add a preference or constraint")
    p.add_argument("--person", required=True)
    p.add_argument("--category", required=True,
                   choices=["work-style", "technical", "communication", "personal"])
    p.add_argument("--description", required=True)
    p.add_argument("--strength", required=True, choices=["hard", "soft"])

    # add-life-event
    p = sub.add_parser("add-life-event", help="Add a career/personal milestone")
    p.add_argument("--person", required=True)
    p.add_argument("--type", required=True,
                   choices=["job-start","job-end","publication","conference",
                            "project-launch","education-start","education-end","award"])
    p.add_argument("--date", required=True, help="ISO datetime e.g. 2020-01-15T00:00:00")
    p.add_argument("--description", required=True)

    # add-topic
    p = sub.add_parser("add-topic", help="Add a topic/interest area")
    p.add_argument("--person", required=True)
    p.add_argument("--name", required=True)
    p.add_argument("--description")
    p.add_argument("--importance", default="medium", choices=["high","medium","low"])
```

In `main()`, update dispatch to:

```python
    dispatch = {
        "create-profile": cmd_create_profile,
        "add-goal":        cmd_add_goal,
        "add-preference":  cmd_add_preference,
        "add-life-event":  cmd_add_life_event,
        "add-topic":       cmd_add_topic,
    }
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_agent_os.py::TestManualEntry -v
```

Expected: All 5 tests pass.

- [ ] **Step 5: Commit**

```bash
git add skills/agent-os/agent_os.py tests/test_agent_os.py
git commit -m "feat(agent-os): add manual entry commands (add-goal, add-preference, add-life-event, add-topic)"
```

---

## Task 4: Context Retrieval (get-context, show-profile, show-ingestion)

**Files:**
- Modify: `skills/agent-os/agent_os.py`
- Modify: `tests/test_agent_os.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/test_agent_os.py`:

```python
class TestContextRetrieval:
    """Tests for get-context, show-profile, show-ingestion."""

    TEST_TAG = uuid.uuid4().hex[:8]
    goal_id = None
    pref_id = None
    event_id = None
    topic_id = None

    @classmethod
    def setup_class(cls):
        run_cmd("create-profile", "--person", OPERATOR_ID)
        r = run_cmd("add-goal", "--person", OPERATOR_ID,
                    "--description", f"Test goal for context {cls.TEST_TAG}",
                    "--priority", "2")
        cls.goal_id = r["id"]
        r = run_cmd("add-preference", "--person", OPERATOR_ID,
                    "--category", "technical",
                    "--description", f"Test pref {cls.TEST_TAG}",
                    "--strength", "soft")
        cls.pref_id = r["id"]
        r = run_cmd("add-life-event", "--person", OPERATOR_ID,
                    "--type", "conference",
                    "--date", "2025-06-01T00:00:00",
                    "--description", f"Test event {cls.TEST_TAG}")
        cls.event_id = r["id"]
        r = run_cmd("add-topic", "--person", OPERATOR_ID,
                    "--name", f"Test Topic {cls.TEST_TAG}",
                    "--importance", "high")
        cls.topic_id = r["id"]

    @classmethod
    def teardown_class(cls):
        if cls.goal_id:
            typedb_delete(f'match $g isa aos-goal, has id "{cls.goal_id}"; '
                          '$r (profile: $p, goal: $g) isa aos-profile-has-goal; '
                          'delete $r; delete $g;')
        if cls.pref_id:
            typedb_delete(f'match $p isa aos-preference, has id "{cls.pref_id}"; '
                          '$r (profile: $pr, preference: $p) isa aos-profile-has-preference; '
                          'delete $r; delete $p;')
        if cls.event_id:
            typedb_delete(f'match $e isa aos-life-event, has id "{cls.event_id}"; '
                          '$r (profile: $p, event: $e) isa aos-profile-has-life-event; '
                          'delete $r; delete $e;')
        if cls.topic_id:
            typedb_delete(f'match $t isa aos-topic, has id "{cls.topic_id}"; delete $t;')

    def test_get_context_goals(self):
        result = run_cmd("get-context", "--person", OPERATOR_ID, "--dimension", "goals")
        assert "goals" in result
        ids = [g["id"] for g in result["goals"]]
        assert self.goal_id in ids

    def test_get_context_preferences(self):
        result = run_cmd("get-context", "--person", OPERATOR_ID, "--dimension", "preferences")
        assert "preferences" in result
        ids = [p["id"] for p in result["preferences"]]
        assert self.pref_id in ids

    def test_get_context_career(self):
        result = run_cmd("get-context", "--person", OPERATOR_ID, "--dimension", "career")
        assert "life_events" in result
        ids = [e["id"] for e in result["life_events"]]
        assert self.event_id in ids

    def test_get_context_topics(self):
        result = run_cmd("get-context", "--person", OPERATOR_ID, "--dimension", "topics")
        assert "topics" in result
        ids = [t["id"] for t in result["topics"]]
        assert self.topic_id in ids

    def test_get_context_all(self):
        result = run_cmd("get-context", "--person", OPERATOR_ID, "--dimension", "all")
        for key in ["goals", "preferences", "life_events", "topics", "interactions", "health"]:
            assert key in result

    def test_show_profile(self):
        result = run_cmd("show-profile", "--person", OPERATOR_ID)
        assert "person" in result
        assert result["person"]["id"] == OPERATOR_ID
        assert "profile_id" in result

    def test_show_ingestion(self):
        result = run_cmd("show-ingestion", "--person", OPERATOR_ID)
        assert "ingestion" in result
        # No sources ingested yet — should return empty list or dict
        assert isinstance(result["ingestion"], (list, dict))
```

- [ ] **Step 2: Run to confirm failures**

```bash
pytest tests/test_agent_os.py::TestContextRetrieval -v
```

Expected: All fail with `"Unknown command"`.

- [ ] **Step 3: Implement `cmd_get_context`, `cmd_show_profile`, `cmd_show_ingestion`**

Add before `build_parser()` in `agent_os.py`:

```python
def cmd_get_context(args):
    """Return structured context JSON for a person."""
    pid = escape_string(args.person)
    dimension = args.dimension or "all"

    with get_driver() as driver:
        profile_id = _find_profile(driver, args.person)
        if not profile_id:
            print(json.dumps({"success": False, "error": f"No profile for person '{args.person}'"}))
            return
        pesc = escape_string(profile_id)

        result = {"success": True}

        if dimension in ("goals", "all"):
            with driver.transaction(TYPEDB_DATABASE, TransactionType.READ) as tx:
                rows = list(tx.query(f'''
                    match
                      $profile isa aos-operator-profile, has id "{pesc}";
                      (profile: $profile, goal: $goal) isa aos-profile-has-goal;
                      $goal has id $gid, has description $desc,
                            has aos-priority $pri, has aos-goal-status $status;
                    fetch {{
                      "id": $gid, "description": $desc,
                      "priority": $pri, "status": $status
                    }};
                ''').resolve())
            result["goals"] = [
                {"id": r["id"]["value"], "description": r["description"]["value"],
                 "priority": r["priority"]["value"], "status": r["status"]["value"]}
                for r in rows
            ]

        if dimension in ("preferences", "all"):
            with driver.transaction(TYPEDB_DATABASE, TransactionType.READ) as tx:
                rows = list(tx.query(f'''
                    match
                      $profile isa aos-operator-profile, has id "{pesc}";
                      (profile: $profile, preference: $pref) isa aos-profile-has-preference;
                      $pref has id $pid, has description $desc,
                            has aos-preference-category $cat,
                            has aos-preference-strength $str;
                    fetch {{
                      "id": $pid, "description": $desc,
                      "category": $cat, "strength": $str
                    }};
                ''').resolve())
            result["preferences"] = [
                {"id": r["id"]["value"], "description": r["description"]["value"],
                 "category": r["category"]["value"], "strength": r["strength"]["value"]}
                for r in rows
            ]

        if dimension in ("career", "all"):
            with driver.transaction(TYPEDB_DATABASE, TransactionType.READ) as tx:
                rows = list(tx.query(f'''
                    match
                      $profile isa aos-operator-profile, has id "{pesc}";
                      (profile: $profile, event: $event) isa aos-profile-has-life-event;
                      $event has id $eid, has description $desc,
                              has aos-event-type $etype, has aos-event-date $edate;
                    fetch {{
                      "id": $eid, "description": $desc,
                      "type": $etype, "date": $edate
                    }};
                ''').resolve())
            result["life_events"] = [
                {"id": r["id"]["value"], "description": r["description"]["value"],
                 "type": r["type"]["value"], "date": str(r["date"]["value"])}
                for r in rows
            ]

        if dimension in ("topics", "all"):
            with driver.transaction(TYPEDB_DATABASE, TransactionType.READ) as tx:
                rows = list(tx.query(f'''
                    match $topic isa aos-topic,
                          has id $tid, has name $tname, has aos-importance $imp;
                    fetch {{ "id": $tid, "name": $tname, "importance": $imp }};
                ''').resolve())
            result["topics"] = [
                {"id": r["id"]["value"], "name": r["name"]["value"],
                 "importance": r["importance"]["value"]}
                for r in rows
            ]

        if dimension in ("interactions", "all"):
            with driver.transaction(TYPEDB_DATABASE, TransactionType.READ) as tx:
                rows = list(tx.query(f'''
                    match $i isa alh-interaction, has id $iid, has alh-interaction-type $itype;
                    fetch {{ "id": $iid, "type": $itype }};
                ''').resolve())
            result["interactions"] = [
                {"id": r["id"]["value"], "type": r["type"]["value"]}
                for r in rows
            ]

        if dimension in ("health", "all"):
            with driver.transaction(TYPEDB_DATABASE, TransactionType.READ) as tx:
                rows = list(tx.query(f'''
                    match $h isa aos-health-snapshot,
                          has aos-metric-type $mtype, has aos-metric-value $mval,
                          has aos-metric-date $mdate;
                    fetch {{ "metric_type": $mtype, "value": $mval, "date": $mdate }};
                ''').resolve())
            result["health"] = [
                {"metric_type": r["metric_type"]["value"],
                 "value": r["value"]["value"],
                 "date": str(r["date"]["value"])}
                for r in rows
            ]

    print(json.dumps(result))


def cmd_show_profile(args):
    """Show full structured profile for a person."""
    pid = escape_string(args.person)

    with get_driver() as driver:
        # Person info
        with driver.transaction(TYPEDB_DATABASE, TransactionType.READ) as tx:
            rows = list(tx.query(f'''
                match $p isa alh-person, has id "{pid}", has name $n;
                fetch {{ "id": $p.id, "name": $n }};
            ''').resolve())
        if not rows:
            print(json.dumps({"success": False, "error": f"Person '{args.person}' not found"}))
            return
        person = {"id": rows[0]["id"]["value"], "name": rows[0]["name"]["value"]}

        profile_id = _find_profile(driver, args.person)

    print(json.dumps({
        "success": True,
        "person": person,
        "profile_id": profile_id,
    }))


def cmd_show_ingestion(args):
    """Show last ingestion note per source for a person's profile."""
    with get_driver() as driver:
        profile_id = _find_profile(driver, args.person)
        if not profile_id:
            print(json.dumps({"success": False, "error": f"No profile for '{args.person}'"}))
            return
        pesc = escape_string(profile_id)

        with driver.transaction(TYPEDB_DATABASE, TransactionType.READ) as tx:
            rows = list(tx.query(f'''
                match
                  $profile isa aos-operator-profile, has id "{pesc}";
                  (subject: $profile, note: $note) isa alh-aboutness;
                  $note isa aos-ingestion-note,
                        has aos-ingestion-source $src,
                        has aos-items-processed $count,
                        has created-at $ts;
                fetch {{
                  "source": $src, "items": $count, "last_run": $ts
                }};
            ''').resolve())
        ingestion = [
            {"source": r["source"]["value"],
             "items": r["items"]["value"],
             "last_run": str(r["last_run"]["value"])}
            for r in rows
        ]

    print(json.dumps({"success": True, "ingestion": ingestion}))
```

Update `build_parser()` — add after the `add-topic` parser:

```python
    # get-context
    p = sub.add_parser("get-context", help="Get structured context JSON")
    p.add_argument("--person", required=True)
    p.add_argument("--dimension",
                   choices=["goals","preferences","career","topics","interactions","health","all"],
                   default="all")

    # show-profile
    p = sub.add_parser("show-profile", help="Show full structured profile")
    p.add_argument("--person", required=True)

    # show-ingestion
    p = sub.add_parser("show-ingestion", help="Show last ingestion timestamps per source")
    p.add_argument("--person", required=True)
```

Update `dispatch` in `main()`:

```python
    dispatch = {
        "create-profile":  cmd_create_profile,
        "add-goal":        cmd_add_goal,
        "add-preference":  cmd_add_preference,
        "add-life-event":  cmd_add_life_event,
        "add-topic":       cmd_add_topic,
        "get-context":     cmd_get_context,
        "show-profile":    cmd_show_profile,
        "show-ingestion":  cmd_show_ingestion,
    }
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_agent_os.py::TestContextRetrieval -v
```

Expected: All 7 tests pass.

- [ ] **Step 5: Commit**

```bash
git add skills/agent-os/agent_os.py tests/test_agent_os.py
git commit -m "feat(agent-os): add get-context, show-profile, show-ingestion commands"
```

---

## Task 5: Full Test Run + SKILL.md

**Files:**
- Create: `skills/agent-os/SKILL.md`

- [ ] **Step 1: Run full test suite to confirm all passing**

```bash
pytest tests/test_agent_os.py -v
```

Expected: All tests pass. Note any failures and fix before proceeding.

- [ ] **Step 2: Smoke-test the CLI manually against the live operator**

```bash
# Ensure profile exists for real operator
uv run python skills/agent-os/agent_os.py create-profile --person op-f25ab4b15b0f

# Add a real goal
uv run python skills/agent-os/agent_os.py add-goal \
  --person op-f25ab4b15b0f \
  --description "Ship agent-os skill foundation by end of May 2026" \
  --priority 1

# Get context
uv run python skills/agent-os/agent_os.py get-context \
  --person op-f25ab4b15b0f --dimension goals | python3 -m json.tool
```

Expected: JSON with the new goal visible in the `goals` array.

- [ ] **Step 3: Write `skills/agent-os/SKILL.md`**

```markdown
# agent-os — Operator Context Skill

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
```

- [ ] **Step 4: Final commit**

```bash
git add skills/agent-os/SKILL.md
git commit -m "docs(agent-os): add SKILL.md usage documentation"
```

---

## Verification

After all tasks complete, the following should work end-to-end:

```bash
# Full test suite green
pytest tests/test_agent_os.py -v

# CLI smoke test
uv run python skills/agent-os/agent_os.py create-profile --person op-f25ab4b15b0f
uv run python skills/agent-os/agent_os.py add-goal \
  --person op-f25ab4b15b0f --description "Verify agent-os works" --priority 1
uv run python skills/agent-os/agent_os.py get-context \
  --person op-f25ab4b15b0f --dimension all | python3 -m json.tool

# Schema visible in TypeDB
uv run python -c "
from typedb.driver import Credentials, DriverOptions, TransactionType, TypeDB
with TypeDB.driver('localhost:1729', Credentials('admin','password'), DriverOptions(is_tls_enabled=False)) as d:
    with d.transaction('alhazen_notebook', TransactionType.READ) as tx:
        for t in ['aos-operator-profile','aos-goal','aos-preference',
                  'aos-life-event','aos-topic','aos-email-thread','aos-ingestion-note']:
            r = list(tx.query(f'match \$x sub {t}; fetch {{\"l\": \$x.label;}};').resolve())
            print(t, ':', 'OK' if r else 'MISSING')
"
```

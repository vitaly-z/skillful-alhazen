#!/usr/bin/env python3
"""
agent-os CLI -- large-scale operator context dataset.

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
    return results[0]["id"]


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

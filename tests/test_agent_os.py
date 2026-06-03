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
            f'$bearing isa alh-role-bearing (bearer: $person, borne-role: $p); '
            f'delete $bearing; delete $p;'
        )

    def test_create_profile_idempotent(self):
        """Creating a profile when one exists should return the existing profile."""
        r1 = run_cmd("create-profile", "--person", OPERATOR_ID)
        r2 = run_cmd("create-profile", "--person", OPERATOR_ID)
        assert r1["profile_id"] == r2["profile_id"]
        # Cleanup
        typedb_delete(
            f'match $p isa aos-operator-profile, has id "{r1["profile_id"]}"; '
            f'$bearing isa alh-role-bearing (bearer: $person, borne-role: $p); '
            f'delete $bearing; delete $p;'
        )


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
        # TypeDB 3.x: deleting a role player cascades to the relation
        typedb_delete(f'match $g isa aos-goal, has id "{result["id"]}"; delete $g;')

    def test_add_goal_with_target_date(self):
        desc = f"Test goal with date {self.TEST_TAG}"
        result = run_cmd(
            "add-goal", "--person", OPERATOR_ID,
            "--description", desc,
            "--priority", "1",
            "--target-date", "2026-12-31T00:00:00",
        )
        assert result["id"].startswith("aos-goal-")
        typedb_delete(f'match $g isa aos-goal, has id "{result["id"]}"; delete $g;')

    def test_add_preference(self):
        result = run_cmd(
            "add-preference", "--person", OPERATOR_ID,
            "--category", "technical",
            "--description", f"Prefer TypeDB {self.TEST_TAG}",
            "--strength", "hard",
        )
        assert result["id"].startswith("aos-pref-")
        typedb_delete(f'match $p isa aos-preference, has id "{result["id"]}"; delete $p;')

    def test_add_life_event(self):
        result = run_cmd(
            "add-life-event", "--person", OPERATOR_ID,
            "--type", "job-start",
            "--date", "2020-01-15T00:00:00",
            "--description", f"Started at CZI {self.TEST_TAG}",
        )
        assert result["id"].startswith("aos-event-")
        typedb_delete(f'match $e isa aos-life-event, has id "{result["id"]}"; delete $e;')

    def test_add_topic(self):
        result = run_cmd(
            "add-topic", "--person", OPERATOR_ID,
            "--name", f"Test Topic {self.TEST_TAG}",
            "--description", "A test topic",
            "--importance", "high",
        )
        assert result["id"].startswith("aos-topic-")
        typedb_delete(f'match $t isa aos-topic, has id "{result["id"]}"; delete $t;')


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
            typedb_delete(f'match $g isa aos-goal, has id "{cls.goal_id}"; delete $g;')
        if cls.pref_id:
            typedb_delete(f'match $p isa aos-preference, has id "{cls.pref_id}"; delete $p;')
        if cls.event_id:
            typedb_delete(f'match $e isa aos-life-event, has id "{cls.event_id}"; delete $e;')
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
        # No sources ingested yet -- should return empty list or dict
        assert isinstance(result["ingestion"], (list, dict))

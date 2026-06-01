#!/usr/bin/env python3
"""
TypeDB Notebook CLI - Command-line interface for Alhazen's Notebook knowledge graph.

Usage:
    python scripts/typedb_notebook.py <command> [options]

Commands:
    insert-collection   Create a new collection
    insert-note         Create a note about an entity
    query-collection    Get collection info and members
    query-notes         Find notes about an entity
    tag                 Tag an entity
    search-tag          Search entities by tag

Examples:
    # Create a collection
    python scripts/typedb_notebook.py insert-collection --name "CRISPR Papers" --description "Papers about CRISPR"

    # Add a note about a paper
    python scripts/typedb_notebook.py insert-note --subject paper-abc123 --content "Key finding: 95% efficiency"

    # Query notes about an entity
    python scripts/typedb_notebook.py query-notes --subject paper-abc123

Environment:
    TYPEDB_HOST     TypeDB server host (default: localhost)
    TYPEDB_PORT     TypeDB server port (default: 1729)
    TYPEDB_DATABASE Database name (default: alhazen_notebook)
"""

import argparse
import json
import os
import shutil
import sys
import zipfile
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

try:
    from typedb.driver import Credentials, DriverOptions, TransactionType, TypeDB

    TYPEDB_AVAILABLE = True
except ImportError:
    TYPEDB_AVAILABLE = False
    print(
        "Warning: typedb-driver not installed. Install with: pip install 'typedb-driver>=3.8.0'",
        file=sys.stderr,
    )

try:
    from skillful_alhazen.utils.skill_helpers import escape_string, generate_id
except ImportError:
    # Fallback if package not installed (e.g., running outside uv)
    import uuid

    def escape_string(s: str) -> str:
        if s is None:
            return ""
        return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "")

    def generate_id(prefix: str) -> str:
        return f"{prefix}-{uuid.uuid4().hex[:12]}"


# Configuration
TYPEDB_HOST = os.getenv("TYPEDB_HOST", "localhost")
TYPEDB_PORT = int(os.getenv("TYPEDB_PORT", "1729"))
TYPEDB_DATABASE = os.getenv("TYPEDB_DATABASE", "alhazen_notebook")
TYPEDB_USERNAME = os.getenv("TYPEDB_USERNAME", "admin")
TYPEDB_PASSWORD = os.getenv("TYPEDB_PASSWORD", "password")


def get_driver():
    """Get TypeDB driver connection."""
    return TypeDB.driver(
        f"{TYPEDB_HOST}:{TYPEDB_PORT}",
        Credentials(TYPEDB_USERNAME, TYPEDB_PASSWORD),
        DriverOptions(is_tls_enabled=False),
    )


def insert_collection(args):
    """Create a new collection."""
    cid = args.id or generate_id("collection")

    query = f'insert $c isa alh-collection, has id "{cid}", has name "{escape_string(args.name)}"'
    if args.description:
        query += f', has description "{escape_string(args.description)}"'
    if args.query:
        query += f', has alh-logical-query "{escape_string(args.query)}"'
    query += ";"

    with get_driver() as driver:
        with driver.transaction(TYPEDB_DATABASE, TransactionType.WRITE) as tx:
            tx.query(query).resolve()
            tx.commit()

    print(json.dumps({"success": True, "collection_id": cid, "name": args.name}))



def insert_note(args):
    """Create a note about an entity."""
    nid = args.id or generate_id("note")

    # Insert the note
    query = f'insert $n isa alh-note, has id "{nid}", has content "{escape_string(args.content)}"'
    if args.name:
        query += f', has name "{escape_string(args.name)}"'
    if args.confidence:
        query += f", has confidence {args.confidence}"
    query += ";"

    with get_driver() as driver:
        with driver.transaction(TYPEDB_DATABASE, TransactionType.WRITE) as tx:
            tx.query(query).resolve()
            tx.commit()

        # Create alh-aboutness relation
        with driver.transaction(TYPEDB_DATABASE, TransactionType.WRITE) as tx:
            rel_query = f'match $s isa alh-identifiable-entity, has id "{args.subject}"; $n isa alh-note, has id "{nid}"; insert (note: $n, subject: $s) isa alh-aboutness;'
            tx.query(rel_query).resolve()
            tx.commit()

        # Add tags if specified
        if args.tags:
            for tag in args.tags:
                tag_id = generate_id("tag")
                with driver.transaction(TYPEDB_DATABASE, TransactionType.WRITE) as tx:
                    try:
                        tx.query(f'insert $t isa alh-tag, has id "{tag_id}", has name "{tag}";').resolve()
                        tx.commit()
                    except Exception:
                        tx.rollback()  # Tag might already exist

                with driver.transaction(TYPEDB_DATABASE, TransactionType.WRITE) as tx:
                    tx.query(
                        f'match $n isa alh-note, has id "{nid}"; $t isa alh-tag, has name "{tag}"; insert (tagged-entity: $n, tag: $t) isa alh-tagging;'
                    ).resolve()
                    tx.commit()

    print(json.dumps({"success": True, "note_id": nid, "subject": args.subject}))


def query_collection(args):
    """Get collection info and members."""
    with get_driver() as driver:
        with driver.transaction(TYPEDB_DATABASE, TransactionType.READ) as tx:
            # Get collection
            result = list(tx.query(
                f'match $c isa alh-collection, has id "{args.id}"; '
                f'fetch {{ "id": $c.id, "name": $c.name, "description": $c.description }};'
            ).resolve())
            if not result:
                print(json.dumps({"success": False, "error": "Collection not found"}))
                return

            # Get members
            members = list(tx.query(
                f'match $c isa alh-collection, has id "{args.id}"; '
                f'(collection: $c, member: $m) isa alh-collection-membership; '
                f'fetch {{ "id": $m.id, "name": $m.name }};'
            ).resolve())

        print(
            json.dumps(
                {
                    "success": True,
                    "collection": {k: v for k, v in result[0].items() if v is not None},
                    "members": [{k: v for k, v in m.items() if v is not None} for m in members],
                    "member_count": len(members),
                },
                indent=2,
            )
        )


def query_notes(args):
    """Find notes about an entity."""
    with get_driver() as driver:
        with driver.transaction(TYPEDB_DATABASE, TransactionType.READ) as tx:
            query = (
                f'match $s isa alh-identifiable-entity, has id "{args.subject}"; '
                f'(note: $n, subject: $s) isa alh-aboutness; '
                f'fetch {{ "id": $n.id, "name": $n.name, "content": $n.content, "confidence": $n.confidence }};'
            )
            results = [{k: v for k, v in r.items() if v is not None}
                       for r in tx.query(query).resolve()]

        print(
            json.dumps(
                {
                    "success": True,
                    "subject": args.subject,
                    "notes": results,
                    "count": len(results),
                },
                indent=2,
            )
        )


def tag_entity(args):
    """Tag an entity."""
    with get_driver() as driver:
        # Create tag if not exists
        tag_id = generate_id("tag")
        with driver.transaction(TYPEDB_DATABASE, TransactionType.WRITE) as tx:
            try:
                tx.query(f'insert $t isa alh-tag, has id "{tag_id}", has name "{args.tag}";').resolve()
                tx.commit()
            except Exception:
                tx.rollback()  # Tag might already exist

        # Create tagging relation
        with driver.transaction(TYPEDB_DATABASE, TransactionType.WRITE) as tx:
            tx.query(
                f'match $e isa alh-identifiable-entity, has id "{args.entity}"; $t isa alh-tag, has name "{args.tag}"; insert (tagged-entity: $e, tag: $t) isa alh-tagging;'
            ).resolve()
            tx.commit()

    print(json.dumps({"success": True, "entity": args.entity, "tag": args.tag}))


def search_tag(args):
    """Search entities by tag."""
    with get_driver() as driver:
        with driver.transaction(TYPEDB_DATABASE, TransactionType.READ) as tx:
            query = (
                f'match $t isa alh-tag, has name "{args.tag}"; '
                f'(tagged-entity: $e, tag: $t) isa alh-tagging; '
                f'fetch {{ "id": $e.id, "name": $e.name }};'
            )
            results = [{k: v for k, v in r.items() if v is not None}
                       for r in tx.query(query).resolve()]

        print(
            json.dumps(
                {
                    "success": True,
                    "tag": args.tag,
                    "entities": results,
                    "count": len(results),
                },
                indent=2,
            )
        )


def record_gap(args):
    """Record a schema gap for a skill."""
    with get_driver() as driver:
        # Upsert slog-skill-model
        with driver.transaction(TYPEDB_DATABASE, TransactionType.READ) as tx:
            check = list(tx.query(
                f'match $s isa slog-skill-model, has slog-skill-name "{escape_string(args.skill)}"; fetch {{ "id": $s.id }};'
            ).resolve())

        if check:
            skill_id = check[0]["id"]
        else:
            skill_id = generate_id("slog-skill-model")
            with driver.transaction(TYPEDB_DATABASE, TransactionType.WRITE) as tx:
                tx.query(
                    f'insert $s isa slog-skill-model, has id "{skill_id}", has name "{escape_string(args.skill)}", '
                    f'has slog-skill-name "{escape_string(args.skill)}";'
                ).resolve()
                tx.commit()

        # Insert slog-schema-gap
        gap_id = generate_id("gap")
        severity = getattr(args, "severity", "moderate") or "moderate"
        query = (
            f'insert $g isa slog-schema-gap, has id "{gap_id}", '
            f'has name "{escape_string(args.skill)}: {escape_string(args.type)}", '
            f'has description "{escape_string(args.description)}", '
            f'has slog-gap-type "{escape_string(args.type)}", '
            f'has slog-gap-severity "{severity}", '
            f'has slog-gap-status "open"'
        )
        if args.example:
            query += f', has slog-gap-example "{escape_string(args.example)}"'
        query += ";"

        with driver.transaction(TYPEDB_DATABASE, TransactionType.WRITE) as tx:
            tx.query(query).resolve()
            tx.commit()

        # Link gap to slog-skill-model
        with driver.transaction(TYPEDB_DATABASE, TransactionType.WRITE) as tx:
            tx.query(
                f'match $s isa slog-skill-model, has id "{skill_id}"; $g isa slog-schema-gap, has id "{gap_id}"; '
                f'insert (slog-skill-model: $s, slog-schema-gap: $g) isa slog-skill-has-gap;'
            ).resolve()
            tx.commit()

    print(json.dumps({"success": True, "gap_id": gap_id, "skill": args.skill, "type": args.type}))


def list_gaps(args):
    """List schema gaps, optionally filtered by skill and/or status."""
    with get_driver() as driver:
        with driver.transaction(TYPEDB_DATABASE, TransactionType.READ) as tx:
            skill_filter = ""
            if hasattr(args, "skill") and args.skill:
                skill_filter = f'$s isa slog-skill-model, has slog-skill-name "{escape_string(args.skill)}"; '

            status_filter = ""
            if hasattr(args, "status") and args.status:
                status_filter = f'$g has slog-gap-status "{escape_string(args.status)}"; '
            else:
                status_filter = '$g has slog-gap-status "open"; '

            if skill_filter:
                query = (
                    f'match {skill_filter}(slog-skill-model: $s, slog-schema-gap: $g) isa slog-skill-has-gap; '
                    f'{status_filter}'
                    f'fetch {{ "id": $g.id, "type": $g.slog-gap-type, "severity": $g.slog-gap-severity, '
                    f'"status": $g.slog-gap-status, "description": $g.description, "example": $g.slog-gap-example }};'
                )
            else:
                query = (
                    f'match $g isa slog-schema-gap; {status_filter}'
                    f'fetch {{ "id": $g.id, "type": $g.slog-gap-type, "severity": $g.slog-gap-severity, '
                    f'"status": $g.slog-gap-status, "description": $g.description, "example": $g.slog-gap-example }};'
                )

            results = [{k: v for k, v in r.items() if v is not None}
                       for r in tx.query(query).resolve()]

    print(json.dumps({"success": True, "gaps": results, "count": len(results)}, indent=2))


def close_gap(args):
    """Update a gap's status to addressed or wont-fix."""
    with get_driver() as driver:
        # Delete old status, insert new
        with driver.transaction(TYPEDB_DATABASE, TransactionType.WRITE) as tx:
            tx.query(
                f'match $g isa slog-schema-gap, has id "{args.id}", has slog-gap-status $s; '
                f'delete $s;'
            ).resolve()
            tx.commit()

        with driver.transaction(TYPEDB_DATABASE, TransactionType.WRITE) as tx:
            tx.query(
                f'match $g isa slog-schema-gap, has id "{args.id}"; '
                f'insert $g has slog-gap-status "{escape_string(args.status)}";'
            ).resolve()
            tx.commit()

    print(json.dumps({"success": True, "gap_id": args.id, "status": args.status}))


def export_db(args):
    """Export the full TypeDB database using the TypeDB Python driver API."""
    if not TYPEDB_AVAILABLE:
        print(json.dumps({"success": False, "error": "typedb-driver not installed"}))
        return

    database = args.database or TYPEDB_DATABASE

    # Build timestamped folder name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder_name = f"{database}_export_{timestamp}"

    # Determine cache directory
    cache_dir_env = os.getenv("ALHAZEN_CACHE_DIR")
    if cache_dir_env:
        cache_dir = Path(cache_dir_env).expanduser()
    else:
        cache_dir = Path.home() / ".alhazen" / "cache"
    export_dir = cache_dir / "typedb" / folder_name
    export_dir.mkdir(parents=True, exist_ok=True)

    schema_file = f"{database}_schema.typeql"
    data_file = f"{database}_data.typedb"
    local_schema = export_dir / schema_file
    local_data = export_dir / data_file

    print(f"Exporting database '{database}' via Python driver...", file=sys.stderr)

    with get_driver() as driver:
        db = driver.databases.get(database)
        db.export_to_file(str(local_schema), str(local_data))

    # Create zip archive
    zip_path = export_dir.parent / f"{folder_name}.zip"
    print(f"Creating zip archive...", file=sys.stderr)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for filepath in export_dir.iterdir():
            zf.write(filepath, f"{folder_name}/{filepath.name}")

    # Get file sizes
    schema_size = local_schema.stat().st_size
    data_size = local_data.stat().st_size
    zip_size = zip_path.stat().st_size

    # Remove unzipped folder (keep only the zip)
    shutil.rmtree(export_dir)

    print(json.dumps({
        "success": True,
        "database": database,
        "timestamp": timestamp,
        "zip_path": str(zip_path),
        "zip_size": zip_size,
        "contents": {
            "schema": {"file": schema_file, "size": schema_size},
            "data": {"file": data_file, "size": data_size},
        },
    }, indent=2))


def import_db(args):
    """Import a TypeDB database from a previously exported zip using the Python driver API."""
    if not TYPEDB_AVAILABLE:
        print(json.dumps({"success": False, "error": "typedb-driver not installed"}))
        return

    zip_path = Path(args.zip).expanduser()
    if not zip_path.exists():
        print(json.dumps({"success": False, "error": f"File not found: {zip_path}"}))
        return

    database = args.database

    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(tmpdir)

        # Find the schema and data files
        schema_file = None
        data_file = None
        for f in tmpdir.rglob("*"):
            if f.suffix == ".typeql":
                schema_file = f
            elif f.suffix == ".typedb":
                data_file = f

        if not schema_file or not data_file:
            print(json.dumps({
                "success": False,
                "error": "Zip must contain one .typeql (schema) and one .typedb (data) file"
            }))
            return

        print(f"Importing database '{database}' via Python driver...", file=sys.stderr)

        schema_text = schema_file.read_text()

        with get_driver() as driver:
            driver.databases.import_from_file(database, schema_text, str(data_file))

    print(json.dumps({
        "success": True,
        "database": database,
        "source": str(zip_path),
    }, indent=2))


# -----------------------------------------------------------------------------
# Analysis pipeline notes (stored, re-runnable Hamilton workflows)
# -----------------------------------------------------------------------------
# A note that subtypes alh-analysis-pipeline-note stores a Hamilton module's
# source (alh-pipeline-script) + a JSON config (alh-pipeline-config). The generic
# runner reloads the module, builds the DAG, executes the requested terminal
# outputs, and writes each result back to the attribute named by the config's
# output_attr_map (default: content). Pipeline notes link to their source
# collections (the input data) via alh-aboutness.

_PIPELINE_ID_PREFIXES = {
    "scilit-faceting-note": "scfn",
    "alh-analysis-pipeline-note": "apn",
}


def _read_arg_or_file(value: str) -> str:
    """Return the literal value, or the file contents if value starts with '@'."""
    if value.startswith("@"):
        with open(value[1:]) as f:
            return f.read()
    return value


def load_pipeline_module(source_code: str, module_name: str = "alh_pipeline"):
    """Dynamically load a Hamilton pipeline module from a source-code string.

    Uses a real temp file + importlib because Hamilton's introspection calls
    inspect.getsource(), which requires a path on disk.
    """
    import importlib.util
    import tempfile

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", prefix=f"{module_name}_", delete=False
    ) as f:
        f.write(source_code)
        tmp_path = f.name
    spec = importlib.util.spec_from_file_location(module_name, tmp_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    os.unlink(tmp_path)
    return mod


def create_pipeline_note(args):
    """Create an analysis-pipeline note (or subtype) and link it to source collections."""
    note_type = args.type
    prefix = _PIPELINE_ID_PREFIXES.get(note_type, "pnote")
    nid = args.id or generate_id(prefix)

    script = _read_arg_or_file(args.script)
    config = _read_arg_or_file(args.config)
    try:
        json.loads(config)
    except json.JSONDecodeError as e:
        print(json.dumps({"success": False, "error": f"--config is not valid JSON: {e}"}))
        sys.exit(1)

    now = datetime.now().isoformat(timespec="seconds")
    collection_ids = [c.strip() for c in args.collections.split(",") if c.strip()] if args.collections else []

    query = (
        f'insert $n isa {note_type}, has id "{nid}", '
        f'has alh-pipeline-script "{escape_string(script)}", '
        f'has alh-pipeline-config "{escape_string(config)}", '
        f'has created-at {now}'
    )
    if args.name:
        query += f', has name "{escape_string(args.name)}"'
    query += ";"

    linked = []
    with get_driver() as driver:
        with driver.transaction(TYPEDB_DATABASE, TransactionType.WRITE) as tx:
            tx.query(query).resolve()
            tx.commit()

        for cid in collection_ids:
            with driver.transaction(TYPEDB_DATABASE, TransactionType.WRITE) as tx:
                rel = (
                    f'match $n isa {note_type}, has id "{nid}"; '
                    f'$c isa alh-identifiable-entity, has id "{escape_string(cid)}"; '
                    f'insert (note: $n, subject: $c) isa alh-aboutness;'
                )
                tx.query(rel).resolve()
                tx.commit()
            linked.append(cid)

    print(json.dumps({
        "success": True,
        "note_id": nid,
        "type": note_type,
        "linked_collections": linked,
        "script_chars": len(script),
    }))


def run_pipeline_note(args):
    """Execute a stored Hamilton pipeline note and write terminal outputs back."""
    nid = escape_string(args.id)
    with get_driver() as driver:
        # Fetch script + config (polymorphic: isa includes subtypes)
        with driver.transaction(TYPEDB_DATABASE, TransactionType.READ) as tx:
            results = list(tx.query(
                f'match $n isa alh-analysis-pipeline-note, has id "{nid}"; '
                f'fetch {{ "script": $n.alh-pipeline-script, "config": $n.alh-pipeline-config }};'
            ).resolve())

        if not results:
            print(json.dumps({"success": False, "error": f"Pipeline note {args.id} not found"}))
            sys.exit(1)

        script = results[0].get("script")
        config_str = results[0].get("config")
        if not script:
            print(json.dumps({"success": False, "error": "Note has no alh-pipeline-script"}))
            sys.exit(1)
        if not config_str:
            print(json.dumps({"success": False, "error": "Note has no alh-pipeline-config"}))
            sys.exit(1)

        config = json.loads(config_str)
        outputs = config.get("outputs", [])
        if not outputs:
            print(json.dumps({"success": False, "error": "config has no 'outputs' list"}))
            sys.exit(1)

        # Resolve inputs (explicit + env-sourced)
        inputs = dict(config.get("inputs", {}))
        for param_name, env_var in config.get("env_inputs", {}).items():
            val = os.environ.get(env_var)
            if val is None:
                print(json.dumps({"success": False, "error": f"Required env var {env_var} (for '{param_name}') is not set"}))
                sys.exit(1)
            inputs[param_name] = val

        try:
            from hamilton import driver as h_driver  # noqa: PLC0415
        except ImportError:
            print(json.dumps({"success": False, "error": "sf-hamilton not installed. Run: uv add sf-hamilton"}))
            sys.exit(1)

        print("Loading pipeline module...", file=sys.stderr)
        mod = load_pipeline_module(script, module_name=f"pipeline_{nid}")

        hamilton_cfg = config.get("hamilton", {})
        builder = h_driver.Builder().with_modules(mod)
        if hamilton_cfg.get("with_cache"):
            builder = builder.with_cache()
        dr = builder.build()

        print(f"Executing Hamilton outputs: {outputs}", file=sys.stderr)
        results_map = dr.execute(outputs, inputs=inputs)

        # Write terminal outputs back per output_attr_map (default -> content)
        output_attr_map = config.get("output_attr_map", {})
        written = {}
        non_persisted = {}
        with driver.transaction(TYPEDB_DATABASE, TransactionType.WRITE) as tx:
            for output_name, value in results_map.items():
                attr_name = output_attr_map.get(output_name)
                if attr_name is None:
                    # Not mapped to an attribute: report but don't persist
                    non_persisted[output_name] = value if isinstance(value, (int, float, str, dict, list, bool)) else str(value)
                    continue
                if not isinstance(value, str):
                    value = json.dumps(value)
                escaped_val = escape_string(value)
                tx.query(
                    f'match $n isa alh-analysis-pipeline-note, has id "{nid}", has {attr_name} $old; '
                    f'delete has $old of $n;'
                ).resolve()
                tx.query(
                    f'match $n isa alh-analysis-pipeline-note, has id "{nid}"; '
                    f'insert $n has {attr_name} "{escaped_val}";'
                ).resolve()
                written[output_name] = {"attr": attr_name, "chars": len(value)}
            tx.commit()

        print(json.dumps({
            "success": True,
            "note_id": args.id,
            "outputs_written": written,
            "outputs_not_persisted": non_persisted,
        }))


def show_pipeline_note(args):
    """Round-trip a pipeline note: script, parsed config, and content."""
    nid = escape_string(args.id)
    with get_driver() as driver:
        with driver.transaction(TYPEDB_DATABASE, TransactionType.READ) as tx:
            results = list(tx.query(
                f'match $n isa alh-analysis-pipeline-note, has id "{nid}"; '
                f'fetch {{ "name": $n.name, "script": $n.alh-pipeline-script, '
                f'"config": $n.alh-pipeline-config, "content": $n.content }};'
            ).resolve())

    if not results:
        print(json.dumps({"success": False, "error": f"Pipeline note {args.id} not found"}))
        sys.exit(1)

    r = results[0]
    config_str = r.get("config")
    out = {
        "success": True,
        "note_id": args.id,
        "name": r.get("name"),
        "script": r.get("script"),
        "config": json.loads(config_str) if config_str else None,
        "content": r.get("content"),
    }
    print(json.dumps(out, indent=2))


def main():
    parser = argparse.ArgumentParser(
        description="TypeDB Notebook CLI for Alhazen's knowledge graph"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # insert-collection
    p = subparsers.add_parser("insert-collection", help="Create a new collection")
    p.add_argument("--name", required=True, help="Collection name")
    p.add_argument("--description", help="Collection description")
    p.add_argument("--query", help="Logical query defining membership")
    p.add_argument("--id", help="Specific ID (auto-generated if not provided)")

    # insert-note
    p = subparsers.add_parser("insert-note", help="Create a note about an entity")
    p.add_argument("--subject", required=True, help="ID of entity this note is about")
    p.add_argument("--content", required=True, help="Note content")
    p.add_argument("--name", help="Note name/title")
    p.add_argument("--confidence", type=float, help="Confidence score (0.0-1.0)")
    p.add_argument("--tags", nargs="+", help="Tags to apply")
    p.add_argument("--id", help="Specific ID")

    # query-collection
    p = subparsers.add_parser("query-collection", help="Get collection info")
    p.add_argument("--id", required=True, help="Collection ID")

    # query-notes
    p = subparsers.add_parser("query-notes", help="Find notes about an entity")
    p.add_argument("--subject", required=True, help="Entity ID")

    # tag
    p = subparsers.add_parser("tag", help="Tag an entity")
    p.add_argument("--entity", required=True, help="Entity ID")
    p.add_argument("--tag", required=True, help="Tag name")

    # search-tag
    p = subparsers.add_parser("search-tag", help="Search by tag")
    p.add_argument("--tag", required=True, help="Tag to search for")

    # record-gap
    p = subparsers.add_parser("record-gap", help="Record a schema/model gap for a skill")
    p.add_argument("--skill", required=True, help="Skill name (e.g., 'jobhunt')")
    p.add_argument(
        "--type", required=True,
        choices=["missing-user-context", "missing-entity-type", "missing-attribute",
                 "unclear-workflow", "incorrect-inference"],
        help="Gap type",
    )
    p.add_argument("--description", required=True, help="What information is missing or wrong")
    p.add_argument(
        "--severity", choices=["minor", "moderate", "significant"], default="moderate",
        help="Gap severity (default: moderate)",
    )
    p.add_argument("--example", help="The specific triggering situation")

    # list-gaps
    p = subparsers.add_parser("list-gaps", help="List schema gaps")
    p.add_argument("--skill", help="Filter by skill name")
    p.add_argument("--status", choices=["open", "addressed", "wont-fix"],
                   help="Filter by status (default: open)")

    # close-gap
    p = subparsers.add_parser("close-gap", help="Mark a gap as addressed or wont-fix")
    p.add_argument("--id", required=True, help="Gap ID")
    p.add_argument("--status", required=True, choices=["addressed", "wont-fix"],
                   help="New status")

    # export-db
    p = subparsers.add_parser("export-db", help="Export database to timestamped zip")
    p.add_argument("--database", help=f"Database name (default: {TYPEDB_DATABASE})")

    # import-db
    p = subparsers.add_parser("import-db", help="Import database from exported zip")
    p.add_argument("--zip", required=True, help="Path to the export zip file")
    p.add_argument("--database", required=True, help="Target database name (must not exist)")

    # create-pipeline-note
    p = subparsers.add_parser(
        "create-pipeline-note",
        help="Store a Hamilton pipeline as a note and link it to source collections",
    )
    p.add_argument("--type", default="alh-analysis-pipeline-note",
                   help="Note type (subtype of alh-analysis-pipeline-note; default: alh-analysis-pipeline-note)")
    p.add_argument("--script", required=True, help="Hamilton module source (or @path/to/module.py)")
    p.add_argument("--config", required=True, help="JSON config (or @path/to/config.json)")
    p.add_argument("--collections", help="Comma-separated source collection IDs (linked via alh-aboutness)")
    p.add_argument("--name", help="Note name/title")
    p.add_argument("--id", help="Specific ID (auto-generated if not provided)")

    # run-pipeline-note
    p = subparsers.add_parser("run-pipeline-note", help="Execute a stored pipeline note and write outputs back")
    p.add_argument("--id", required=True, help="Pipeline note ID")

    # show-pipeline-note
    p = subparsers.add_parser("show-pipeline-note", help="Show a pipeline note's script, config, and content")
    p.add_argument("--id", required=True, help="Pipeline note ID")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if not TYPEDB_AVAILABLE:
        print(json.dumps({"success": False, "error": "typedb-driver not installed"}))
        sys.exit(1)

    commands = {
        "insert-collection": insert_collection,
        "insert-note": insert_note,
        "query-collection": query_collection,
        "query-notes": query_notes,
        "tag": tag_entity,
        "search-tag": search_tag,
        "record-gap": record_gap,
        "list-gaps": list_gaps,
        "close-gap": close_gap,
        "export-db": export_db,
        "import-db": import_db,
        "create-pipeline-note": create_pipeline_note,
        "run-pipeline-note": run_pipeline_note,
        "show-pipeline-note": show_pipeline_note,
    }

    try:
        commands[args.command](args)
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()

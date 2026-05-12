# First-Time Infrastructure Setup

> **For agents:** Follow these steps in order. Each step includes a verification command. Do not proceed to the next step until the verification passes.

## 1. Prerequisites

Verify all prerequisites before attempting the build:

```bash
# uv (Python package manager) — must print a version string
uv --version
# If missing: curl -LsSf https://astral.sh/uv/install.sh | sh

# Docker (container runtime) — must succeed without errors
docker info
# If failing: start Docker Desktop (macOS) or `sudo systemctl start docker` (Linux)

# Docker Compose v2 (bundled with Docker Desktop) — must print "Docker Compose version v2.x.x"
docker compose version
# NOTE: use `docker compose` (with a space), NOT the old `docker-compose` (with hyphen)

# git — must print a version string
git --version
```

**macOS:** Docker Desktop includes Docker Compose v2 — just start Docker Desktop.
**Linux:** Install `docker-compose-plugin` (not the standalone `docker-compose` v1).

## 2. Full Build (recommended)

```bash
make build
```

Runs four steps in sequence: `build-env` → `build-skills` → `build-dashboard` → `build-db`.
If any step fails, run the individual steps below to diagnose.

## 3. Individual Steps with Verification

### Step 1: Install Python dependencies

```bash
make build-env
# Verify the TypeDB driver is importable:
uv run python -c "import typedb.driver; print('typedb driver OK')"
```

Expected output: `typedb driver OK`. If the import fails, run `uv sync --all-extras` directly and read any error output.

### Step 2: Resolve skills from registry

```bash
make build-skills
# Verify that all skills are present in local_skills/:
ls local_skills/
```

Expected: directories for `typedb-notebook`, `web-search`, `curation-skill-builder`, `jobhunt`, `techrecon`, `scientific-literature`, and others listed in `skills-registry.yaml`. If external skills are absent, network access to `https://github.com/sciknow-io/alhazen-skill-examples` may have failed — run `make skills-update` to retry.

### Step 3: Start TypeDB and load schemas

```bash
make build-db
# Verify the container is running and healthy:
docker ps --filter "name=alhazen-typedb" --format "table {{.Names}}\t{{.Status}}"
```

Expected: `alhazen-typedb` with status containing `(healthy)`. The `db-start` target waits up to 60 seconds for TypeDB readiness before running `db-init`. Each `.tql` schema file prints `OK` when loaded successfully.

## 4. Post-Build Smoke Test

```bash
# Check overall status (TypeDB container + skills count):
make status

# Write a test collection to TypeDB (confirms full read/write connectivity):
uv run python .claude/skills/typedb-notebook/typedb_notebook.py insert-collection --name "smoke-test"
```

Expected: `make status` shows TypeDB running. The insert-collection command returns JSON with `"success": true`.

## 5. Optional: Semantic Search (Qdrant)

The `scientific-literature` skill requires Qdrant for embedding-based search. It is **not** started by `make build` — start it separately only when needed:

```bash
make qdrant-start           # starts Qdrant on http://localhost:6333
export VOYAGE_API_KEY=<key> # from https://dash.voyageai.com/
```

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `docker info` fails | Docker not running | Open Docker Desktop (macOS) or `sudo systemctl start docker` (Linux) |
| `make build-db` hangs > 60s | TypeDB slow to start | `docker logs alhazen-typedb`; increase Docker memory in Desktop settings |
| Port 1729 in use | Another TypeDB instance | `docker ps -a \| grep 1729` then `docker stop <id>` |
| External skills absent from `local_skills/` | Git clone failed silently | `make skills-update` to retry; check network/git access |
| Schema fails `[SYR1] type not found` | Missing `entity` keyword in `.tql` | See TypeDB 3.x notes — add `entity` keyword before type name |
| Schema fails `sub attribute` syntax error | Stale 2.x schema in external skill | See External Skill Schema Fixes below |
| TypeDB auth error in Python | Wrong credentials | Default: username=`admin`, password=`password` (no `.env` setup needed) |
| Queries return empty after adding new skill | Schema not reloaded | Re-run `make db-init` after `make build-skills` adds a new skill |

## Environment Management

**This project uses [uv](https://docs.astral.sh/uv/) for Python dependency management.**

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install all dependencies (creates .venv automatically)
uv sync --all-extras

# Run a script with dependencies
uv run python script.py

# Add a new dependency
uv add package-name

# Update dependencies
uv sync
```

All dependencies are defined in `pyproject.toml`. The `.venv` directory is created automatically by uv.

## Environment Variables

**TypeDB:**
- `TYPEDB_HOST` - TypeDB server host (default: `localhost`)
- `TYPEDB_PORT` - TypeDB server port (default: `1729`)
- `TYPEDB_DATABASE` - Database name (default: `alhazen_notebook`)
- `TYPEDB_USERNAME` - TypeDB username (default: `admin`) — no setup needed for local Docker
- `TYPEDB_PASSWORD` - TypeDB password (default: `password`) — no setup needed for local Docker

**Cache:**
- `ALHAZEN_CACHE_DIR` - File cache directory for large artifacts (default: ~/.alhazen/cache)

**Semantic Search (literature skill):**
- `VOYAGE_API_KEY` - Voyage AI API key for embeddings (from https://dash.voyageai.com/)
- `QDRANT_HOST` - Qdrant vector store host (default: localhost)
- `QDRANT_PORT` - Qdrant vector store port (default: 6333)

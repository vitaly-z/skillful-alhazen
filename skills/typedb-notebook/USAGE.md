# TypeDB Notebook — Usage Reference

## Core Memory Operations

### Remember (insert-note)

Store information in the knowledge graph for later retrieval. Use this whenever you learn something worth remembering about a paper, concept, or any research topic.

**Triggers:** "remember this", "remember that", "save this", "note that", "store", "make a note", "don't forget", "keep track of"

```bash
uv run python .claude/skills/typedb-notebook/typedb_notebook.py insert-note \
    --subject "paper-xyz789" \
    --content "Key finding: 95% editing efficiency in liver cells. Uses novel lipid nanoparticle delivery." \
    --name "Key Findings" \
    --confidence 0.9 \
    --tags crispr liver high-efficiency
```

**Options:**
- `--subject` (required): ID of the entity this note is about
- `--content` (required): The note content
- `--name`: Optional title for the note
- `--confidence`: Confidence score (0.0-1.0)
- `--tags`: Space-separated list of tags
- `--id`: Specific ID (auto-generated if not provided)

Returns: `{"success": true, "note_id": "note-abc123", "subject": "paper-xyz789"}`

Notes can be about:
- Papers (paper-*)
- Other notes (note-*) - for meta-commentary or synthesis
- Collections (collection-*)
- Any entity in the knowledge graph

### Recall (query-notes)

Query the knowledge graph for previously stored information. Use this when you need to remember what you've learned about something.

**Triggers:** "what do I know about", "what did I learn about", "recall", "remember", "find notes about", "what notes do I have", "retrieve"

```bash
uv run python .claude/skills/typedb-notebook/typedb_notebook.py query-notes --subject "paper-xyz789"
```

Returns:
```json
{
  "success": true,
  "subject": "paper-xyz789",
  "notes": [...],
  "count": 3
}
```

---

## Corpus Building Operations

### Build Corpus (insert-collection)

Create a collection of papers/documents for analysis. Collections can be defined extensionally (explicit members) or intensionally (by a logical query).

**Triggers:** "create collection", "build corpus", "gather papers", "collect papers", "create a set of", "group these papers", "make a collection"

```bash
uv run python .claude/skills/typedb-notebook/typedb_notebook.py insert-collection \
    --name "CRISPR Research" \
    --description "Papers about CRISPR gene editing" \
    --query "CRISPR AND (gene editing OR Cas9)"
```

**Options:**
- `--name` (required): Collection name
- `--description`: Collection description
- `--query`: Logical query defining membership (for intensional collections)
- `--id`: Specific ID (auto-generated if not provided)

Returns: `{"success": true, "collection_id": "collection-abc123", "name": "CRISPR Research"}`

### Add Papers to Corpus

To ingest papers from literature sources (PubMed, OpenAlex, Europe PMC), use the **literature** or **epmc-search** skill — those handle domain-specific ingestion into the knowledge graph.

### Query Collection (query-collection)

Get collection details and members.

```bash
uv run python .claude/skills/typedb-notebook/typedb_notebook.py query-collection --id "collection-abc123"
```

Returns:
```json
{
  "success": true,
  "collection": {...},
  "members": [...],
  "member_count": 5
}
```

---

## Classification Operations

### Classify / Tag (tag)

Classify an entity with a tag. Use this to categorize papers by topic, method, or any other dimension.

**Triggers:** "classify", "categorize", "tag", "label", "mark as", "this is a"

```bash
uv run python .claude/skills/typedb-notebook/typedb_notebook.py tag --entity "paper-xyz789" --tag "high-impact"
```

Returns: `{"success": true, "entity": "paper-xyz789", "tag": "high-impact"}`

### Find by Category (search-tag)

Find all entities matching a category or tag.

**Triggers:** "find all", "show me", "list", "what papers are tagged", "which ones are"

```bash
uv run python .claude/skills/typedb-notebook/typedb_notebook.py search-tag --tag "crispr"
```

Returns:
```json
{
  "success": true,
  "tag": "crispr",
  "entities": [...],
  "count": 12
}
```

---

## Synthesis Operations

### Synthesize

Create a note that summarizes/synthesizes other notes or entities. Use this when you want to combine findings from multiple sources into a coherent summary or analysis.

**Triggers:** "synthesize", "summarize notes", "combine findings", "create summary", "summarize what I know", "bring together"

```bash
# First, query notes to gather information
uv run python .claude/skills/typedb-notebook/typedb_notebook.py query-notes --subject "paper-123"
uv run python .claude/skills/typedb-notebook/typedb_notebook.py query-notes --subject "paper-456"

# Then create a synthesis note about one of the sources (or create a collection first)
uv run python .claude/skills/typedb-notebook/typedb_notebook.py insert-note \
    --subject "collection-abc123" \
    --content "Synthesis: Both papers demonstrate >90% efficiency. Paper-123 uses lipid nanoparticles while paper-456 uses viral vectors. Key difference is delivery mechanism affects tissue targeting." \
    --name "Delivery Methods Synthesis" \
    --tags synthesis delivery-methods comparison
```

### Compare

Create a comparative note about two or more entities.

**Triggers:** "compare", "contrast", "how does X differ from Y", "what's the difference between", "similarities between"

```bash
uv run python .claude/skills/typedb-notebook/typedb_notebook.py insert-note \
    --subject "paper-123" \
    --content "Comparison with paper-456: Both achieve high editing efficiency. Paper-123 is more suitable for liver targeting, paper-456 for systemic delivery." \
    --name "Method Comparison" \
    --tags comparison methods
```

---

## Workflow Examples

### Literature Review Workflow

1. Use `/literature` or `/epmc-search` to ingest papers into the knowledge graph
2. Create notes with key findings for each paper
3. Tag papers by methodology, findings, etc.
4. Create synthesis notes that reference multiple papers

```bash
# 1. Ingest papers via literature skill (see /literature for details)

# 2. Create notes about ingested papers
uv run python .claude/skills/typedb-notebook/typedb_notebook.py insert-note \
    --subject "paper-yyy" \
    --content "Key finding: 95% efficacy in preventing severe disease" \
    --tags efficacy mrna

# 3. Tag papers
uv run python .claude/skills/typedb-notebook/typedb_notebook.py tag --entity "paper-yyy" --tag "high-efficacy"

# 4. Create synthesis
uv run python .claude/skills/typedb-notebook/typedb_notebook.py insert-note \
    --subject "collection-xxx" \
    --content "Summary: mRNA vaccines show consistently high efficacy..." \
    --name "Literature Review Summary" \
    --tags synthesis review
```

### Remember and Recall Pattern

When you learn something worth remembering:
```bash
uv run python .claude/skills/typedb-notebook/typedb_notebook.py insert-note \
    --subject "paper-123" \
    --content "This paper introduces a novel approach to X" \
    --tags important methodology
```

When you need to recall:
```bash
# Recall by subject
uv run python .claude/skills/typedb-notebook/typedb_notebook.py query-notes --subject "paper-123"

# Or search by tag
uv run python .claude/skills/typedb-notebook/typedb_notebook.py search-tag --tag "methodology"
```

---

## Analysis Pipelines (stored, re-runnable Hamilton workflows)

An **analysis-pipeline note** stores *and executes* a [Hamilton](https://hamilton.dagworks.io/)
pipeline. It captures a throwaway analysis script — and the exact inputs it ran on — as a
first-class, re-runnable artifact in the knowledge graph, instead of leaving it in a cache that
gets wiped on system updates.

The capability is built on two attributes of `alh-analysis-pipeline-note` (a subtype of `alh-note`):

- `alh-pipeline-script` — the full source of a self-contained Hamilton module (plain functions;
  Hamilton derives the DAG from each function's **parameter names**).
- `alh-pipeline-config` — a JSON config: `outputs` (terminal nodes to compute), `inputs`
  (values fed to free DAG inputs), optional `env_inputs` (map param → env var), `output_attr_map`
  (terminal node → TypeDB attribute to write the result to; default behaviour writes nothing back
  unless mapped), and optional `hamilton` options (e.g. `{"with_cache": true}`).

Pipeline notes are linked to their **source collections** (the input data) via `alh-aboutness`.
Domain subtypes (e.g. `scilit-faceting-note`) work with the same commands — pass `--type`.

### Create a pipeline note (create-pipeline-note)

```bash
uv run python skills/typedb-notebook/typedb_notebook.py create-pipeline-note \
    --type alh-analysis-pipeline-note \
    --collections collection-abc123,collection-def456 \
    --script @path/to/pipeline_module.py \
    --config @path/to/config.json \
    --name "My analysis"
```

`--script` / `--config` accept an inline string or an `@file` path. Each `--collections` id is
linked to the new note via `alh-aboutness`. Returns the new `note_id`.

### Run a pipeline note (run-pipeline-note)

```bash
uv run python skills/typedb-notebook/typedb_notebook.py run-pipeline-note --id <note-id>
```

Fetches the stored script + config, reloads the module (via a temp file so Hamilton's
`inspect.getsource()` works), builds the DAG with `Builder().with_modules(mod).build()`, executes
`dr.execute(config["outputs"], inputs=…)`, and writes each terminal output back to the attribute
named in `output_attr_map` (delete-has-then-insert). Non-string outputs are JSON-serialized.
Outputs with no `output_attr_map` entry are reported but not persisted.

### Inspect a pipeline note (show-pipeline-note)

```bash
uv run python skills/typedb-notebook/typedb_notebook.py show-pipeline-note --id <note-id>
```

Round-trips the stored `script`, parsed `config`, and computed `content`.

> **Worked example:** the scientific-literature skill's `scilit-faceting-note` is a worked subtype
> that faceting-tags a corpus and computes cross-tabulations. See that skill's USAGE.md.

---

## Generic Graph CRUD Engine

A **schema-validated, generic graph-write layer** so that agents (and skills) mutate the
TypeDB knowledge graph **without authoring raw TypeQL**. You describe *what* to write as
typed entities, attributes, and relations; the engine builds and runs the TypeQL.

**Triggers:** "create entity", "add a node", "set attribute", "update field", "link",
"connect", "relate", "unlink", "delete entity", "run recipe", "apply ops", "what
attributes does X have", "describe the schema for"

### Design (why this exists)

- **Agents never write raw TypeQL.** Every write is expressed as a declarative op and
  compiled by the engine, so escaping, datetime formatting, and `isa` requirements are
  handled centrally and correctly.
- **The schema is learned by static parse, never queried.** A variable-free schema match
  (`match X sub Y;`) *panics TypeDB 3.8 and restarts the container*. Instead, the engine
  parses every `.tql` file (the alh-core base + each namespace schema listed in
  `skills-registry.yaml`) into a `SchemaModel`. The model knows every type's supertype
  chain, owned attributes (transitively), value types, multi-valued cardinality, and the
  roles each relation defines / each entity plays.
- **Validation is up front.** Unknown type, abstract type, unknown/unowned attribute,
  invalid relation role, single-valued attribute given multiple values — all rejected
  *before* any write touches the database.
- **`apply` is atomic.** Every op in one `apply` runs inside **one** write transaction and
  commits once. If any op fails, nothing is written.
- **Reads are guarded.** `query` requires a bound variable and a `fetch { ... }` clause and
  rejects write keywords — so a read can never crash the server or mutate data.

### Inspect the schema (describe-schema)

Look up what a type owns / plays, or get a global summary. **Read-only, no DB access** —
it only parses the `.tql` files, so it's always safe to run.

```bash
# One type
uv run python skills/typedb-notebook/typedb_notebook.py describe-schema --type scilit-evidence

# Global summary (counts + sorted lists of all types)
uv run python skills/typedb-notebook/typedb_notebook.py describe-schema
```

A single-type result reports the `kind` (`entity` | `relation` | `attribute`), its
`supertype_chain`, every owned `attribute` (`value_type`, `key`, `multi`), and (for
entities) the `plays` list of `(relation, role)` pairs:

```json
{
  "success": true,
  "type": "scilit-evidence",
  "kind": "entity",
  "abstract": false,
  "supertype_chain": ["scilit-evidence", "alh-note", "alh-information-content-entity", "alh-identifiable-entity"],
  "attributes": [
    {"name": "scilit-evidence-type", "value_type": "string", "key": false, "multi": false},
    {"name": "id", "value_type": "string", "key": true, "multi": false}
  ],
  "plays": [
    {"relation": "alh-note-threading", "role": "parent-note"},
    {"relation": "alh-note-threading", "role": "child-note"}
  ]
}
```

Use `describe-schema` first whenever you are unsure of an exact attribute name, value
type, or which role connects two entities.

### The op-list model (apply)

`apply` runs an ordered list of ops in one atomic transaction. This is the engine's core;
the per-verb commands below are just convenience wrappers that build a 1-op list.

```bash
uv run python skills/typedb-notebook/typedb_notebook.py apply --dry-run --ops '[
  {"op": "create", "type": "scilit-claim",    "as": "cl", "attrs": {"name": "Claim A", "scilit-claim-type": "primary"}},
  {"op": "create", "type": "scilit-evidence", "as": "ev", "attrs": {"name": "Ev 1", "scilit-evidence-type": "experimental"}},
  {"op": "link", "relation": "alh-note-threading", "roles": {"parent-note": "$cl", "child-note": "$ev"}}
]'
```

`--ops` accepts an inline JSON array **or** an `@path/to/ops.json` file. Add `--dry-run` to
print the compiled TypeQL (and the resolved `bindings`) without writing anything:

```json
{
  "success": true, "dry_run": true, "ops": 3,
  "queries": [
    "insert $e isa scilit-claim, has id \"scilit-claim-a12e…\", has name \"Claim A\", …;",
    "insert $e isa scilit-evidence, has id \"scilit-evidence-37c…\", …;",
    "match $p0 isa alh-identifiable-entity, has id \"scilit-claim-a12e…\"; $p1 isa alh-identifiable-entity, has id \"scilit-evidence-37c…\"; insert (parent-note: $p0, child-note: $p1) isa alh-note-threading;"
  ],
  "bindings": {"cl": "scilit-claim-a12e…", "ev": "scilit-evidence-37c…"}
}
```

**Bindings (`as` / `$ref`)** are the key feature: `"as": "cl"` records the id minted by a
`create`, and any later op can reference it with `"$cl"` — in an attribute value, an `id`,
or a relation role. Because reads inside a write transaction see prior uncommitted writes,
a `create` then `link` in the same `apply` just works.

**Op vocabulary:**

| `op` | Required keys | Notes |
|------|---------------|-------|
| `create` | `type`, `attrs` | Mints an id (or pass `id`); rejects abstract types. `as` binds the id. `created-at` is auto-stamped if the type owns it. |
| `upsert` | `type`, `id`, `attrs` | `create` if the id is absent, else `set-attr`. **Requires an explicit `id`.** |
| `set-attr` | `id`, `attrs` | Sets/updates attributes. Single-valued attrs auto-replace; pass `"replace": true` to clear a multi-valued set first. |
| `delete-attr` | `id`, `attrs` | `{"attr": "val"}` removes one value; `{"attr": null}` (or empty) removes **all** values of that attr. |
| `link` | `relation`, `roles` | `roles` is `{role: entity-id}`. Relation `attrs` optional. `"idempotent": true` no-ops if the relation already exists. |
| `unlink` | `relation`, `roles` | Deletes the matching relation. |
| `delete` | `id` | Deletes the entity. `"detach": true` unlinks its relations first (otherwise TypeDB refuses if it still plays roles). |

Validation errors are returned per op with the offending index, e.g.:

```json
{"success": false, "error": "op[0] (create): unknown attribute 'bogus-attr'"}
{"success": false, "error": "op[0] (create): cannot create instance of abstract type 'alh-information-content-entity'"}
{"success": false, "error": "op[0] (upsert): upsert requires an explicit id"}
```

### Per-verb CLI wrappers

Each builds a single-op `apply`. All accept `--dry-run`. `--attr` and `--role` are
repeatable `key=value` pairs (split on the first `=`).

```bash
# create-entity — mint a typed entity (returns its id)
uv run python skills/typedb-notebook/typedb_notebook.py create-entity \
    --type scilit-claim \
    --attr name="My claim" --attr scilit-claim-type=primary
# -> {"success": true, "ops": 1, "id": "scilit-claim-afe9…", "bindings": {"_new": "scilit-claim-afe9…"}, ...}

# create-entity --upsert (requires --id): create if absent, else set its attrs
uv run python skills/typedb-notebook/typedb_notebook.py create-entity \
    --type scilit-claim --id scilit-claim-abc --upsert --attr name="Renamed"

# set-attr — set/append attributes (--replace clears a multi-valued set first)
uv run python skills/typedb-notebook/typedb_notebook.py set-attr \
    --id scilit-claim-abc --attr scilit-claim-statement="Updated text"

# delete-attr — remove one value (key=value) or all values of a key (key only)
uv run python skills/typedb-notebook/typedb_notebook.py delete-attr \
    --id scilit-claim-abc --attr scilit-claim-statement

# link / unlink — create or remove a relation
uv run python skills/typedb-notebook/typedb_notebook.py link \
    --relation alh-note-threading \
    --role parent-note=note-abc --role child-note=note-def --idempotent

uv run python skills/typedb-notebook/typedb_notebook.py unlink \
    --relation alh-note-threading \
    --role parent-note=note-abc --role child-note=note-def

# delete-entity — delete (--detach unlinks its relations first)
uv run python skills/typedb-notebook/typedb_notebook.py delete-entity \
    --id scilit-claim-abc --detach
```

> `set-attr` writes a delete-has-then-insert per attribute. For a `--dry-run` of `set-attr`
> on a multi-valued attribute, pass `--type` so the engine can check cardinality without
> hitting the DB (when actually writing, it resolves the concrete type from the live id).

### Read-only queries (query)

Run a guarded `match … fetch` query. The query **must** bind a variable and **must**
contain a `fetch { ... }` clause; any write keyword (`insert`, `delete`, `define`,
`undefine`, `update`, `put`) is rejected.

```bash
uv run python skills/typedb-notebook/typedb_notebook.py query --limit 50 --read \
  'match $c isa scilit-claim, has name $n; fetch { "id": $c.id, "name": $n };'
# -> {"success": true, "count": N, "rows": [ {...}, ... ]}
```

Guards (no DB access on rejection):

```json
{"success": false, "error": "read query must contain a `fetch { ... }` clause"}
{"success": false, "error": "write keyword 'insert' not allowed in read query"}
```

`--limit` defaults to 1000.

### Recipes (apply-recipe)

A **recipe** is a named, reusable op-list template with `{{param}}` placeholders — the way
domain skills package a multi-step graph operation. `apply-recipe` resolves a recipe by
name from any `recipes/` directory under `skills/` or `local_skills/`, substitutes params,
and runs the resulting op-list through the same atomic engine.

```bash
uv run python skills/typedb-notebook/typedb_notebook.py apply-recipe \
    --recipe create-deep-dive \
    --param name="GLP-1 mechanism" \
    --param purpose="Deep dive on the focal review" \
    --param focal_paper=scilit-paper-123 \
    --param status=active
```

**Recipe file format** (`<name>.json` in a skill's `recipes/` dir):

```json
{
  "name": "create-deep-dive",
  "description": "Create a deep-dive investigation about a single focal paper …",
  "params": ["name", "purpose", "focal_paper", "status"],
  "ops": [
    {"op": "create", "type": "scilit-investigation", "as": "inv",
     "attrs": {"name": "{{name}}", "content": "{{purpose}}",
               "scilit-investigation-status": "{{status}}",
               "scilit-investigation-type": "deep-dive"}},
    {"op": "link", "relation": "alh-aboutness",
     "roles": {"note": "$inv", "subject": "{{focal_paper}}"}},
    {"op": "create", "type": "scilit-corpus", "as": "corpus",
     "attrs": {"name": "{{name}} - papers", "alh-is-extensional": "false"}},
    {"op": "link", "relation": "alh-aboutness", "roles": {"note": "$inv", "subject": "$corpus"}},
    {"op": "link", "relation": "alh-collection-membership", "idempotent": true,
     "roles": {"collection": "$corpus", "member": "{{focal_paper}}"}}
  ]
}
```

- A string that is exactly `"{{key}}"` is replaced by the param's **raw** value; a
  placeholder embedded in a larger string is replaced textually.
- `params` declares required params — a missing one is reported before any write.
- `as`/`$ref` bindings work across recipe ops exactly as in `apply`.
- `--dry-run` prints the compiled TypeQL per op.

Domain recipes live in their **own** skill's `recipes/` directory (e.g.
`local_skills/scientific-literature/recipes/`). For external skills, the `recipes/` dir is
maintained **upstream** (e.g. `alhazen-skill-examples`) — fixes there must go upstream, or
`make skills-update` will overwrite them.

---

## Data Model

- **Collection**: Groups of papers/items (extensional or intensional)
- **Research-Item / Paper**: Scientific publications (`scilit-paper`) — ingested via literature/epmc-search skills
- **Note**: Your observations and findings (can be about anything, including other notes)
- **Tag**: Lightweight classification labels

---

## Command Reference

| Command | Description | Required Args |
|---------|-------------|---------------|
| `insert-collection` | Create a collection | `--name` |
| `insert-note` | Create a note | `--subject`, `--content` |
| `query-collection` | Get collection info | `--id` |
| `query-notes` | Find notes about entity | `--subject` |
| `tag` | Tag an entity | `--entity`, `--tag` |
| `search-tag` | Search by tag | `--tag` |
| `create-pipeline-note` | Store a Hamilton pipeline as a note | `--script`, `--config` |
| `run-pipeline-note` | Execute a stored pipeline, write outputs back | `--id` |
| `show-pipeline-note` | Show a pipeline's script, config, content | `--id` |
| `describe-schema` | Inspect a type, or a global schema summary (read-only) | _(none; `--type` optional)_ |
| `create-entity` | Create (or `--upsert`) a typed entity | `--type` |
| `set-attr` | Set/append attributes on an entity | `--id`, `--attr` |
| `delete-attr` | Remove an attribute value (or all values of a key) | `--id`, `--attr` |
| `link` | Create a relation between entities | `--relation`, `--role` |
| `unlink` | Delete a relation between entities | `--relation`, `--role` |
| `delete-entity` | Delete an entity (`--detach` unlinks first) | `--id` |
| `query` | Guarded read-only `match … fetch` query | `--read` |
| `apply` | Run an ordered op-list in one atomic transaction | `--ops` |
| `apply-recipe` | Run a named recipe (op-list template) atomically | `--recipe` |
| `export-db` | Export database to timestamped zip | `--database` |
| `import-db` | Import database from zip | `--zip`, `--database` |

---

## Database Export and Import

Export the full database for backup or migration to another TypeDB instance. Exports are saved as timestamped zips in the artifact cache (`~/.alhazen/cache/typedb/`).

### Export (export-db)

**Triggers:** "export database", "backup database", "dump database", "save database"

```bash
uv run python .claude/skills/typedb-notebook/typedb_notebook.py export-db \
    --database alhazen_notebook
```

**Options:**
- `--database`: Database name (default: from `TYPEDB_DATABASE` env var)
- `--container`: Docker container name (default: `alhazen-typedb`)
- `--port`: TypeDB port (default: 1729)

**Output:** Creates a zip at `~/.alhazen/cache/typedb/<database>_export_<YYYYMMDD_HHMMSS>.zip`

Returns:
```json
{
  "success": true,
  "database": "alhazen_notebook",
  "timestamp": "20260208_182846",
  "zip_path": "/Users/you/.alhazen/cache/typedb/alhazen_notebook_export_20260208_182846.zip",
  "zip_size": 192745
}
```

### Import (import-db)

**Triggers:** "import database", "restore database", "load database backup"

The target database **must not already exist**. TypeDB creates it during import.

```bash
uv run python .claude/skills/typedb-notebook/typedb_notebook.py import-db \
    --zip ~/.alhazen/cache/typedb/alhazen_notebook_export_20260208_182846.zip \
    --database alhazen_notebook_restored
```

**Options:**
- `--zip` (required): Path to the export zip file
- `--database` (required): Target database name (must not exist)
- `--container`: Docker container name (default: `alhazen-typedb`)
- `--port`: TypeDB port (default: 1729)

**Notes:**
- Export/import must use the same TypeDB version
- These commands use Docker CLI, not the TypeDB Python driver

---

## TypeDB Reference

When writing custom queries, consult:

- **This Skill's Schema:** `local_skills/typedb-notebook/schema.tql` (if exists)
- **Core Schema:** `local_resources/typedb/alhazen_notebook.tql`

### Common Pitfalls (TypeDB 3.x)

- **Fetch syntax** — Use `fetch { "key": $var.attr };` (JSON-style, NOT `fetch $var: attr1;`)
- **No sessions** — Use `driver.transaction(database, TransactionType.X)` directly
- **Update = delete + insert** — Can't modify attributes in place
- **Fetch results are plain dicts** — No `.get("value")` unwrapping needed

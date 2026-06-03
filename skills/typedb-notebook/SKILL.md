---
name: typedb-notebook
description: Store and retrieve knowledge in the Alhazen TypeDB knowledge graph - remember, recall, organize papers and notes
---

# TypeDB Notebook Skill

Use this skill to store and retrieve knowledge in the Alhazen TypeDB knowledge graph. This allows you to remember information about papers, create notes, and recall them later.

**When to use:** "remember this", "save this", "note that", "store", "don't forget", "what do I know about", "recall", "find notes about", "retrieve", "create collection", "build corpus", "gather papers", "classify", "tag", "synthesize", "compare"

## Generic Graph CRUD

This skill also provides a **schema-validated, generic graph CRUD engine** so agents mutate
the knowledge graph **without authoring raw TypeQL**. Describe writes as declarative,
schema-checked ops — typed entities, attributes, and relations — and the engine compiles and
runs the TypeQL in one atomic transaction. Commands: `describe-schema`, `create-entity`,
`set-attr`, `delete-attr`, `link`, `unlink`, `delete-entity`, `query` (guarded read-only),
`apply` (atomic op-list), `apply-recipe` (named op-list template). See **USAGE.md → Generic
Graph CRUD Engine** for the op vocabulary, bindings, and recipe format.

**When to use:** "create entity", "add a node", "set attribute", "update field", "link",
"connect", "relate", "unlink", "delete entity", "run recipe", "apply ops", "describe the
schema for", "what attributes does X have"

## Prerequisites

- TypeDB must be running: `make db-start`
- Dependencies installed: `uv sync --all-extras` (from project root)

## Environment Variables

- `TYPEDB_HOST`: TypeDB server (default: localhost)
- `TYPEDB_PORT`: TypeDB port (default: 1729)
- `TYPEDB_DATABASE`: Database name (default: alhazen_notebook)

## Quick Start

```bash
# Remember something
uv run python .claude/skills/typedb-notebook/typedb_notebook.py insert-note \
    --subject "paper-xyz789" \
    --content "Key finding: 95% editing efficiency in liver cells."

# Recall it later
uv run python .claude/skills/typedb-notebook/typedb_notebook.py query-notes --subject "paper-xyz789"
```

## Command Output Pattern

`uv run` emits a `VIRTUAL_ENV` warning to stderr. Always use `2>/dev/null` when piping output to a JSON parser — never `2>&1`, which merges the warning into stdout and breaks JSON parsing.

**Before executing any commands, read `USAGE.md` in this directory for the complete command reference, workflows, and data model.**

# Schema Evolution

When a schema gap requires changing existing entity types (hierarchy changes, attribute renames, type consolidation), use the declarative migration workflow instead of manual TypeQL `redefine`:

## Workflow

1. **Detect** — Schema gap found (by agent, skilllog hook, or manual review)
2. **Save old schema** — Copy the current `.tql` file before editing:
   ```bash
   cp local_resources/typedb/alhazen_notebook.tql \
      local_resources/typedb/migration-rules/<migration-name>/old_schema.tql
   ```
3. **Fix the schema** — Edit the `.tql` file with the desired changes
4. **Write intent file** — Describe what changed and why:
   ```yaml
   # local_resources/typedb/migration-rules/<migration-name>/intent.yaml
   renames:
     - old: jhunt-contact-email
       new: alh-email-address
       reason: "Standardized on core person attribute"
   hierarchy_changes:
     - type: jhunt-contact
       old_parent: agent
       new_parent: person
       reason: "Contacts are people, should inherit person attributes"
   ```
5. **Generate rules** — Produce migration mapping rules:
   ```bash
   uv run python src/skillful_alhazen/utils/schema_diff.py diff \
     --old local_resources/typedb/migration-rules/<migration-name>/old_schema.tql \
     --new local_resources/typedb/alhazen_notebook.tql \
     --generate-rules \
     --rules-dir local_resources/typedb/migration-rules/<migration-name>/ \
     --intent local_resources/typedb/migration-rules/<migration-name>/intent.yaml
   ```
6. **Test** — Run against temporary databases (iterative):
   ```bash
   make db-migrate-test RULES=local_resources/typedb/migration-rules/<migration-name>/
   # Read errors, fix rules, re-run until clean
   make db-migrate-test-clean   # when done testing
   ```
7. **Migrate** — Run against production:
   ```bash
   make db-migrate RULES=local_resources/typedb/migration-rules/<migration-name>/
   ```
8. **Verify** — Check reconciliation output, query migrated data

## Key Commands

```bash
# Parse and inspect a schema file
uv run python src/skillful_alhazen/utils/schema_diff.py parse --schema FILE.tql

# Diff two schemas (JSON output)
uv run python src/skillful_alhazen/utils/schema_diff.py diff --old OLD.tql --new NEW.tql

# Diff with human-readable summary
uv run python src/skillful_alhazen/utils/schema_diff.py diff --old OLD.tql --new NEW.tql --summary

# Generate migration rules
uv run python src/skillful_alhazen/utils/schema_diff.py diff \
  --old OLD.tql --new NEW.tql \
  --generate-rules --rules-dir RULES_DIR/ [--intent INTENT.yaml]

# Test migration (non-destructive, iterative)
make db-migrate-test RULES=RULES_DIR/

# Run migration (production)
make db-migrate RULES=RULES_DIR/

# Clean up test databases
make db-migrate-test-clean
```

## Why Not redefine?

TypeDB 3.x `redefine` cannot reliably change entity hierarchies when existing data uses inherited `owns` declarations. The declarative migration approach (export -> new schema -> map data -> verify) is safer and produces an auditable trail of rules.

## Preferred Migration Method: Binary Backup + Query Transfer

When the GLAV schema_mapper approach is too complex (many entity types, unclear attribute mappings), use the **binary backup + query transfer** method:

1. **Export** current database via `make db-export` (binary backup preserves all data + schema)
2. **Import** the backup as a temporary source database:
   ```bash
   uv run python .claude/skills/typedb-notebook/typedb_notebook.py import-db \
     --zip ~/.alhazen/cache/typedb/alhazen_notebook_export_LATEST.zip \
     --database alhazen_backup
   ```
3. **Drop and recreate** the main database with the new schema:
   ```bash
   # Delete main DB
   uv run python -c "
   from typedb.driver import TypeDB, Credentials, DriverOptions
   d = TypeDB.driver('localhost:1729', Credentials('admin','password'), DriverOptions(is_tls_enabled=False))
   d.databases.get('alhazen_notebook').delete(); d.close()"
   # Recreate with new schema
   make db-init
   ```
4. **Query the backup** to re-insert data into the new database. Write targeted TypeQL queries that read from `alhazen_backup` and insert into `alhazen_notebook`:
   ```python
   # Read from backup (old schema — data is intact)
   with driver.transaction("alhazen_backup", TransactionType.READ) as tx:
       results = list(tx.query('match $p isa jhunt-position, has id $id, has name $n; fetch { "id": $id, "name": $n };').resolve())

   # Write to new database (new schema)
   with driver.transaction("alhazen_notebook", TransactionType.WRITE) as tx:
       for r in results:
           tx.query(f'insert $p isa jhunt-position, has id "{r["id"]}", has name "{r["name"]}";').resolve()
       tx.commit()
   ```
5. **Clean up** the backup database when satisfied

**Why this works:** The binary backup preserves data with the old schema intact. Queries against the backup use the old schema's type inference (which works correctly for its own data). The new database has a clean schema loaded from the `.tql` files. You transfer data entity-by-entity using explicit attribute names — no generic `has $a` patterns.

**Why not generic export?** TypeDB's `has $a` (match any attribute) pattern breaks when additive `define` statements have corrupted type inference. Always use explicit attribute names (`has name $n, has id $id`) when querying.

**When to use which approach:**
- **GLAV schema_mapper** — best for systematic migrations with clear attribute mappings (renames, type consolidation). Produces auditable YAML rules. Use `make db-migrate` / `make db-migrate-test`.
- **Binary backup + query transfer** — best for quick migrations, exploratory schema changes, or when you have too many entity types for hand-written rules. More manual but avoids the schema_mapper's rule-writing overhead.
- **Both together** — use binary backup as the source database for schema_mapper rules. This is what `make db-migrate` does internally.

## GLAV for External Data Integration

The GLAV (Global-as-View / Local-as-View) methodology behind `schema_mapper.py` is not limited to schema migration — it is a general-purpose **information integration** approach. Use it whenever external data sources need to be imported or linked into the notebook's TypeDB representation:

1. **Build a temporary TypeDB image** of the external database. Load the external data into a separate TypeDB database using the source's native schema (or a minimal schema that captures its structure).
2. **Write YAML mapping rules** that define how the external schema maps to the notebook's `alhazen_notebook.tql` entity types. Each rule is a `(source_match, target_insert)` pair with skolemization for deterministic ID generation.
3. **Run the mapper** from the external database into `alhazen_notebook`:
   ```bash
   uv run python src/skillful_alhazen/utils/schema_mapper.py run \
     --source-db external_source --target-db alhazen_notebook \
     --rules-dir local_resources/typedb/integration-rules/external-name/
   ```
4. **Reconcile** to verify completeness.

This is how the DisMech disease mechanism knowledge graph was originally integrated — an external dataset loaded into a temporary database, then mapped into the notebook's entity hierarchy via declarative rules. The same pattern applies to any external data source: public databases (PubMed, Monarch, ChEMBL), partner data exports, or API-harvested datasets.

**Key principle:** The notebook schema (`alhazen_notebook.tql` + skill schemas) is the **global schema** — the single integrated view. External sources are **local schemas** that get mapped into it. The mapping rules are the explicit, auditable bridge between them.

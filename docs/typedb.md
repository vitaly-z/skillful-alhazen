# TypeDB 3.x Reference

**Current: TypeDB 3.x (3.8.0 server, 3.8.x Python driver)**

Migration from TypeDB 2.x to 3.x was completed Feb 2026. Key changes:
- Docker image: `typedb/typedb:3.8.0` (was `vaticle/typedb:2.25.0`)
- Python driver: `typedb-driver>=3.8.0` (was `typedb-driver>=2.25.0,<3.0.0`)
- No more sessions — use `driver.transaction(database, TransactionType.X)` directly
- Unified query method: `tx.query(query_string).resolve()` for all query types
- Fetch syntax: `fetch { "key": $var.attr };` (JSON-style, replaces `fetch $var: attr1, attr2;`)
- Schema: `attribute X, value T;` syntax (not `X sub attribute, value T;`)
- Abstract sub-entities: `entity X @abstract, sub Y,` (comma after `@abstract`, before `sub`) — **only works when Y is also abstract** (SVL14)
- `agent` is now `sub alh-domain-thing` (inherits description, created-at, etc. from alh-identifiable-entity)

## Connection Pattern (Python)

```python
from typedb.driver import TypeDB, Credentials, DriverOptions, TransactionType

driver = TypeDB.driver(
    f"{TYPEDB_HOST}:{TYPEDB_PORT}",
    Credentials(TYPEDB_USERNAME, TYPEDB_PASSWORD),
    DriverOptions(is_tls_enabled=False),
)

# Write transaction
with driver.transaction(database, TransactionType.WRITE) as tx:
    tx.query("insert $x isa alh-collection, has id 'abc', has name 'Test';").resolve()
    tx.commit()

# Read transaction (fetch returns plain Python dicts)
with driver.transaction(database, TransactionType.READ) as tx:
    results = list(tx.query('''
        match $c isa alh-collection;
        fetch { "id": $c.id, "name": $c.name };
    ''').resolve())
```

## `redefine` for Schema Changes

```typeql
redefine entity agent sub alh-identifiable-entity;  -- in-place schema change without data migration
```

**Data migration note:** TypeDB 2.x `.typedb` binary exports are NOT directly importable into TypeDB 3.x. Data must be re-ingested using the skills after upgrading.

## Query Notes (gotchas and rules)

- **Fetch syntax** - Use `fetch { "key": $var.attr };` JSON-style (NOT `fetch $var: attr1, attr2;` — that is 2.x syntax)
- **Abstract sub-entities** - Syntax is `entity X @abstract, sub Y,` (comma between `@abstract` and `sub`) — **SVL14: Y must also be abstract**; `alh-domain-thing` is concrete so entities subtyping it cannot be `@abstract`
- **No sessions** - Use `driver.transaction(database, TransactionType.X)` directly (no `driver.session(...)` wrapper)
- **All queries use same method** - `tx.query(query_string).resolve()` for insert, fetch, delete, define
- **Fetch results are plain dicts** - No `.get("value")` unwrapping needed; access keys directly
- **Delete entity/relation syntax** - Use `delete $x;` (NOT `delete $x isa type;` — the `isa` qualifier in the delete clause is invalid in 3.x and causes a parse error)
- **Delete has-attribute syntax** - Use `delete has $v of $e;` (NOT `delete $e has attr $v;` — causes "expected OF" parse error)
- **`entity` is reserved in match clauses** - Cannot use `$x isa entity, has id ...` — `entity` is a TypeQL keyword, not a type label. Use `$x isa alh-identifiable-entity, has id ...` to match any entity by id regardless of concrete type
- **Entity inequality** - Cannot compare entity variables with `!=` directly (causes [REP1] error). Compare id attributes: `$a has id $id1; $b has id $id2; $id1 != $id2;`
- **Note linking relation** - Use `(note: $n, subject: $e) isa alh-aboutness` to attach a note to an entity (NOT `isa annotation` — that relation does not exist in the alhazen schema). `alh-identifiable-entity` plays `aboutness:subject`; `note` plays `aboutness:note`
- **Entity keyword required** - New entity type definitions MUST use `entity` keyword: `entity my-type sub alh-domain-thing,` — without it, TypeDB throws `[SYR1] The type 'X' was not found` (even for newly defined types)
- **No limit in fetch** - Fetch queries don't support `limit` modifier; apply limit in Python: `results[:N]`
- **Relations before entities** - Define relations first in namespace schemas so role names resolve when entities use `plays` clauses
- **No @key on custom attrs** - Only the inherited `id @key` works; adding `@key` to namespace attributes causes schema errors
- **TypeQL comparison operators** — In TypeDB 3.x `not {}` clauses (and elsewhere), use `==` for equality comparison, NOT `=`. `$var = "value"` causes a parse error: "expected comparator".
- **Full reference** — Read `local_resources/typedb/llms.txt` on demand before writing queries; full docs at `local_resources/typedb/typedb-3x-reference.md`

## Schema Syntax for New Skills

- Relations at top level: `relation X,` NOT `relation X sub relation,` (sub relation is invalid in 3.x)
- Attributes: `attribute X, value T;` NOT `X sub attribute, value T;`
- Integer type: `value integer` NOT `value long` (long is TypeDB 2.x; 3.x uses integer)
- **CRITICAL: Entity definitions REQUIRE `entity` keyword**: `entity augura-device sub domain-thing,` — without it, TypeDB 3.x throws `[SYR1] The type 'X' was not found` even when defining a NEW type
- **Relations BEFORE entities**: In namespace schemas, define all relations first so role names resolve when entities use `plays` clauses
- **No `@key` on custom attributes in namespace schemas**: Only the inherited `id @key` (from identifiable-entity) works
- Relations do NOT have `id` attributes — cannot fetch `$r.id` where `$r` is a relation; fetch entity attributes instead
- TypeQL parser rejects non-ASCII characters even in comments — use ASCII-only (no special arrows, degree symbols, etc.)

## Relation Attribute Fetch Restriction

- CANNOT fetch attributes from relation variables: `fetch { "freq": $rel.attr };` -> error [FEX1]
- WORKAROUND: Bind the attribute in the match clause instead:
  `(d: $d, p: $p) isa my-rel, has my-attr $attr; fetch { "freq": $attr };`
- Cannot use literal strings in fetch clause: `"type": "causal"` is invalid TypeQL — add in Python
- These patterns cause [FEX1]: `$rel.confidence`, `$rel.apt-frequency-qualifier` etc.

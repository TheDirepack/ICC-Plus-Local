# Type-safe scripting and help

The scripting interface derives field names and value shapes from the pinned ICC Plus 2.10.6 `types.ts` model. Scripts should query the tool instead of guessing field spellings or value types.

Start with machine-readable discovery:

```bash
iccplus-local reference capabilities --brief
iccplus-local reference schema list
iccplus-local reference commands
iccplus-local reference guide typed-authoring
```

Inspect one native model:

```bash
iccplus-local reference fields choice --details
iccplus-local reference schema choice
iccplus-local template choice
```

Generate declarations for a typed client:

```bash
iccplus-local reference types --format typescript --mode native -o iccplus-native.d.ts
iccplus-local reference types --format typescript --mode patch -o iccplus-patch.d.ts
iccplus-local reference types --format python --mode patch -o iccplus_types.py
```

Native mode keeps pinned requiredness. Patch mode makes fields optional for partial updates. Nested native structures use generated types for Scores, Requirements, Addons, Rows, styling, and other known objects instead of collapsing everything to `unknown` dictionaries.

Direct authoring commands validate known values. For example, a boolean field expects a JSON boolean, not the string `"false"`. Arrays and nested objects are checked against the pinned shape when the tool has a declared type for them. Unknown future fields can still be written through explicit compatibility paths when forward compatibility matters.

Use first-class structural commands for common Creator actions. They handle indexes, parent links, fresh IDs, and reference rewrites:

```bash
iccplus-local clone project.json choice_a --parent row_b
iccplus-local reorder project.json point --order p1,p2,p3
# Row sorting is a structure-phase operation; use row_sort in the structure script.
iccplus-local template design export project.json choice_a -o choice-design.json
```

Use `apply` when several edits must succeed or fail together. Its published operation schema covers structural operations as well as field edits:

```bash
iccplus-local reference schema agent-operations
iccplus-local reference schema choice
# or inspect the apply command
iccplus-local reference commands
```

Authoring conveniences do not become project data. Compact effects, style presets, reusable components, and verification metadata compile into ordinary ICC Plus fields. See `CREATOR_TEMPLATE_BOUNDARY.md`.


## Canonical strict batch format

Use `iccplus-agent-ops` for generated automation. The wrapper requires `strict_fields: true`. Put native ICC Plus values under `values`. Unknown native fields are rejected with spelling suggestions and pinned fields are type checked.

The older compatibility operation format intentionally accepts unknown fields under `values`. Do not use that escape hatch in routine LLM-generated edits.

For read automation, `schema inspect-request` describes the `inspect` batch format.

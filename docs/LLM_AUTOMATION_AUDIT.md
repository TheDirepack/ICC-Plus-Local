# LLM automation audit

Version 0.10.0rc3 audits the CLI as an automation interface, not only as an ICC Plus implementation. The target remains ICC Plus 2.10.6 at source commit `a420836248d32043ae45d03f1b93cdcb9e354663`.

## Result

The recommended LLM path is now small enough to use without learning the full CLI.

1. `iccplus-local capabilities --brief`
2. `iccplus-local schema list`
3. `iccplus-local inspect PROJECT` for batched read-only discovery
4. `iccplus-local apply PROJECT` with the `iccplus-agent-ops` format for atomic writes
5. `iccplus-local check PROJECT`
6. `iccplus-local play PROJECT --state STATE` for player-safe runtime work
7. `iccplus-local format PROJECT --style creator` or the ZIP export commands for release output

The larger command set remains available for direct human use and specialized automation. An agent does not need it for the normal authoring loop.

## Audit findings and fixes

### Discovery was too large

The full `capabilities` response is useful as an inventory but wasteful as the first LLM call. rc3 adds `capabilities --brief`, which returns only the pinned target, canonical commands, schema entry points, safety rules, and exit-code contract. `capabilities --section NAME` retrieves one full section without returning the rest.

### Command help lacked meaning

Before rc3, `describe COMMAND` usually returned `description: null`. It exposed argparse syntax but not the command's role. Every top-level command now has a machine-readable summary. `describe` also accepts nested command paths, for example:

```bash
iccplus-local describe style-template apply
```

The description reports whether the command mutates project data, its category, whether it belongs in the recommended agent path, examples when available, and related schemas.

### Protocol schemas were scattered

Native field schemas were discoverable through the CLI, while session and batch schemas had to be found by filename. rc3 adds:

```bash
iccplus-local schema list
iccplus-local schema agent-operations
iccplus-local schema inspect-request
iccplus-local schema session-request
iccplus-local schema runtime-state
```

The wheel contains the protocol schemas, so these commands work after package installation and do not depend on the source checkout.

### Read-only discovery took too many calls

An agent often needs a preflight, a search, one or two entity reads, and a selector preview before writing. rc3 adds `inspect`, which loads the project once and runs those queries as one read-only JSON request.

Supported query operations are `check`, `summary`, `ids`, `list`, `search`, `show`, `get`, and `match`. Each result has its own `ok` flag. A failed query does not mutate anything. The command exits with code 3 if any query fails.

### Forward compatibility was too permissive for an LLM

The original operation format allows unknown fields inside `values`. That is intentional because a human may need to test a field added by a future ICC Plus release. It also means a misspelling could be mistaken for a future field.

rc3 keeps that compatibility format and adds a separate strict format for agents:

```json
{
  "format": "iccplus-agent-ops",
  "format_version": 1,
  "strict_fields": true,
  "operations": [
    {
      "op": "update",
      "kind": "choice",
      "ref": "choice_a",
      "values": {
        "title": "A"
      }
    }
  ]
}
```

In this format, the operation schema rejects unknown operation keys and the runtime rejects unknown native fields under `values`. Pinned fields are still checked against their source-derived value types. A typo such as `titlle` fails with field-name suggestions instead of being written to the project.

Use the older `operations` schema only when an unknown future ICC Plus field is deliberate.

### Successful writes returned too much data

The old batch receipt could echo full edited entities. That becomes expensive when an LLM edits many Choices. An `iccplus-agent-ops` script now defaults to a compact receipt containing operation IDs and counts, validation counts, write status, and the final project summary. It does not echo complete entity bodies.

Use `apply --result-mode full` when debugging requires the old detailed receipt.

### Project writes were not filesystem-atomic

Validation and operation execution were transactional, but the final JSON file replacement used a direct write. rc3 writes project JSON to a temporary file in the destination directory, flushes it, and replaces the destination with `os.replace`. A process interruption should not leave a half-written project file.

Portable runtime-state files already used atomic replacement and keep that behavior.

## Type safety

There are three layers.

- `fields KIND --details` gives source-derived field types and defaults.
- `schema KIND` and `types --format typescript|python` describe native ICC Plus objects.
- `schema agent-operations` and `schema inspect-request` describe the canonical automation envelopes.

The strict operation schema validates operation structure. Native values are type-checked again by the CLI at execution time. JSON Schema cannot fully express "choose this nested object schema based on a sibling `kind` while also preserving every compatibility alias" without making the protocol much larger. Agents that need static validation of a `values` object can validate it separately with `schema KIND` before sending the batch. Runtime validation remains authoritative.

## Output and error contract

Captured normal output is compact JSON by default. Top-level usage, input, JSON, and I/O errors are JSON on stderr. Exit codes are stable:

- 0: success
- 1: malformed input, usage, file, or command error
- 2: static validation or state-integrity failure
- 3: runtime action, scenario assertion, or batched inspection failure
- 4: atomic operation-script failure

The `types` command is the deliberate exception to JSON stdout when no output file is given because its output is compilable TypeScript or Python source.

## Token and round-trip efficiency

The normal LLM authoring cycle can use two substantive calls before validation: one `inspect` request and one `apply` request. `capabilities --brief` and schema discovery are cacheable for the release because the tool and pinned ICC Plus version identify them explicitly.

Do not call full `capabilities` on every turn. Do not call `fields` for fields already present in generated types or a cached schema. Do not ask `show` for an entity when the preceding `inspect` result already contains it.

## Remaining limitations

The CLI is process-based. It does not expose a long-running RPC or MCP server in this package. Scripts should pass argument arrays directly through their process library instead of constructing shell strings.

Browser-only behavior remains browser-only. DOM layout, CSS rendering, audio playback, IndexedDB save slots, dialogs, and image capture still require the official Creator or Viewer. The scripting tool authors the same project data and packages the official viewer rather than pretending to reproduce those browser mechanisms.

The strict agent operation schema does not statically specialize `values` by `kind`. The runtime does check the field catalog and field value types. A caller that wants pre-execution static checking can validate `values` with the matching native schema.

Official web-GUI verification is still a separate release gate. rc3 improves the interface and regression regimen but does not replace the upstream differential pass.

## Audit regression requirements

A release fails the LLM automation audit if any of these become false:

- every top-level command has a machine-readable summary;
- `capabilities --brief` identifies the canonical agent path;
- all protocol schemas are available through `schema` after wheel installation;
- `inspect` can batch the normal read-only discovery operations;
- `iccplus-agent-ops` rejects unknown operation keys and unknown pinned-field names;
- compatibility operations can still carry a deliberate unknown future field;
- agent batches default to compact receipts;
- failed atomic operations leave the project unchanged;
- ordinary project JSON writes use atomic replacement;
- Creator templates, helper components, and verification metadata remain outside final ICC Plus project JSON.

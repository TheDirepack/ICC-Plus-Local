# ID guarantees

The CLI treats real ICC Plus identities as a write-time invariant. Every normal mutation path normalizes identity-bearing objects and rejects duplicate identities before it writes a file. It does not invent identities for structural records that the ICC Plus Creator leaves at `id: ""`.

## What gets an identity

The guarantee applies to authored ICC Plus entities that own an identity field:

- Rows and Backpack Rows use `id`.
- Choices use `id`.
- Selectable Addons use a real `id`. A normal non-selectable Addon uses the Creator's structural `id: ""` default.
- Ordinary Requirements, including nested Requirements and Score Requirements, use the Creator's structural `id: ""` default rather than a project-wide identity.
- Scores use `idx`.
- Point Types, Variables, Words, Groups, Global Requirements, Row design groups, Choice design groups, and Sound Effects use `id`.
- Categories use the native pair `(type, idx)`.

The project index treats only source-identity-bearing records as global identities. Structural blank IDs on ordinary Requirements and non-selectable Addons are valid and are not duplicate-ID errors.

## Identity fields are not reference fields

Not every field named `id` owns a new identity.

A Score's native `id` points to a Point Type. Its own identity is `idx`.

ICC Plus runtime discount records use `Discount.id` to point back to the Choice that created the discount. The runtime creates those records. The CLI does not allocate a new ID for them.

Fields such as `reqId`, `parentId`, Group member arrays, effect target arrays, and similar values are references to other entities.

The guarantee is therefore "every authored identity-bearing entity has a unique identity," not "every object-shaped record has a globally new string in every field named id."

## Generated IDs

Missing identities are generated deterministically only for entity kinds that own a real ICC Plus identity. Structural blank IDs on ordinary Requirements and non-selectable Addons stay blank. If a generated identity base is already taken, the allocator adds a suffix.

The allocator reserves explicit IDs before it generates missing ones. An automatic ID will not steal an explicit ID that appears later in the input.

Generated IDs are stable for the same input structure and order. They are intended to be readable enough for logs and repair scripts.

For public projects, explicit semantic IDs are still preferable for important Rows and Choices because they survive title rewrites and make shared build data easier to understand.

## Duplicate behavior

Explicit duplicate identities are errors. The CLI does not silently rename one side.

This applies during normalization, direct edits, atomic operation scripts, and repeatable builds. If an operation creates a duplicate identity, the write fails and the original file remains unchanged.

Use:

```bash
iccplus-local ids project.json --all
```

for a complete identity inventory, or:

```bash
```

for the normal preflight check.

## Duplicate mechanics are different

Two ordinary Requirements can still encode the same Requirement even though both carry the structural blank ID. Two different Score `idx` values can still encode the same Score. Those are mechanical duplicates rather than identity collisions.

Validation warns about common duplicate Requirement and Score mechanics. It does not delete them automatically because repeated mechanics can be deliberate in unusual projects.

Set-like Group and design-group membership lists are safer to normalize. `normalize` removes repeated members and rebuilds the reverse membership links.

## Repairing an old project

Run:

```bash
iccplus-local normalize old-project.json -o normalized.json
iccplus-local ids normalized.json --all
iccplus-local validate normalized.json
```

`normalize` fills missing real identities and fixes index and membership bookkeeping. It leaves structural blank Requirement and non-selectable Addon IDs alone. It does not invent a new identity for an explicit duplicate. An explicit collision must be resolved deliberately, normally with `rename` so known references are rewritten.

## ID policy for generated projects

A practical policy is:

- assign explicit semantic IDs to public Rows, important Choices, Point Types, Variables, Groups, and other objects that scripts will refer to often;
- let the CLI generate Score `idx` values and other true identities when naming them adds no value; leave ordinary Requirement and non-selectable Addon `id` fields at the source-compatible blank default;
- never derive public IDs from display order;
- use `rename` for deliberate ID migrations instead of raw string replacement;
- run `check` after every generated or bulk-edited pass.

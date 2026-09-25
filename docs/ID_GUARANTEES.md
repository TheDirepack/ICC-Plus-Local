# ID guarantees

ICC Plus Local treats real ICC Plus identities as a write-time invariant. Normal writes reject duplicate identities. Official hydration fills safe Creator defaults but never invents a missing entity identity.

## What owns an identity

- Rows and Backpack Rows use `id`.
- Choices use `id`.
- Selectable Addons use a real `id`.
- Ordinary non-selectable Addons keep the Creator structural `id: ""`.
- Ordinary Requirements also keep structural `id: ""`.
- Scores use `idx`; Score `id` references a Point Type.
- Point Types, Variables, Words, Groups, Global Requirements, Row Design Groups, Choice Design Groups, and Sound Effects use `id`.
- Categories use the native `(type, idx)` pair.

Reference fields such as `reqId`, `parentId`, Group member arrays, and effect target arrays do not create new identities.

## Generated and public IDs

When an authoring path creates an identity-bearing entity, generated identities are deterministic and avoid explicit IDs already present in the input. Structural blank IDs stay blank.

Prefer explicit semantic IDs for public Rows, important Choices, Points, Variables, Groups, and other objects used by scripts, tests, shared builds, or external tools. Do not derive public IDs from display order.

Explicit duplicate identities are errors. Do not silently rename one side.

## Inspect and repair

Use `inspect` for identity and reference discovery. Use `project ids export` when an interchangeable ID inventory is needed.

For a supported sparse or older ICC Plus 2 project:

```bash
iccplus-local project hydrate old-project.json -o hydrated.json
iccplus-local project validate hydrated.json
```

Hydration does not resolve explicit duplicate IDs. Resolve an intentional ID migration through the current `structure` schema so known references move with it.

Normal `structure`, `rules`, and `style` writes already validate before replacement. Do not add a legacy `check` step after every write.

## Mechanical duplicates

Two blank-ID Requirements can still encode the same Requirement, and two different Score identities can still encode the same mechanical Score. Those are mechanical duplicates rather than identity collisions. Audit them separately instead of treating every repetition as an ID failure.

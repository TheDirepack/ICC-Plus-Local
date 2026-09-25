# Source notes

ICC Plus Local 0.10.0rc11 targets ICC Plus 2.10.6.

- Distribution repository: `wahaha303/ICCPlus`.
- Creator and Viewer source: `wahaha303/ICC-Plus-Svelte`.
- Pinned source commit: `a420836248d32043ae45d03f1b93cdcb9e354663`.
- Current audit date: 2026-09-23.

The field catalog and generated type metadata are checked against the pinned `types.ts`. Runtime behavior is checked against the Viewer store and related Viewer components. Creator source is used for factory defaults, copy/clone behavior, style/design import rules, categories, Build Form serialization, Row buttons, project export, and other authoring actions.

The returned official-GUI verification material includes one strong Creator result: the C01 Save to Disk artifact exactly matches the pinned 2.10.6 round-trip fixture. Other returned cases provide partial evidence but do not complete the current structured browser-verification gate. The local verifier therefore keeps official Creator/Viewer verification separate from the local regression suite.

rc11 adds a normalized player-safe hierarchy to `play`. Visible Rows, direct Choices, and Addons are returned as separate entity lists with explicit parent/child IDs. This changes how an agent can inspect the player surface, but it does not weaken the visibility boundary. Hidden content and private runtime state remain excluded.

This package is an independent local command-line implementation. It does not bundle the ICC Plus browser application or claim that browser-only rendering, media playback, IndexedDB, screenshots, and modal behavior have been reproduced by the headless runner. The official Creator and Viewer remain the authority for final browser behavior and release verification.

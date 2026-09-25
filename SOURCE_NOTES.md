# Source notes

ICC Plus Local 0.10.0rc12 targets ICC Plus 2.10.7.

- Distribution repository: `wahaha303/ICCPlus`.
- Creator and Viewer source: `wahaha303/ICC-Plus-Svelte`.
- Pinned source commit: `1ea9db888cde2286d18d0d5de50933cb8773b739`.
- Current audit date: 2026-09-25.

The field catalog and generated type metadata are checked against the pinned `types.ts`. Runtime behavior is checked against the Viewer store and related Viewer components. Creator source is used for factory defaults, copy/clone behavior, style/design import rules, categories, Build Form serialization, Row buttons, project export, and other authoring actions.

The strongest returned official-GUI Creator artifact remains the earlier 2.10.6 C01 Save to Disk round-trip match. The 2.10.7 upgrade is source-audited against its single upstream commit: the blank project shape is unchanged apart from the version, while Score gains optional `removeSpace` and the Point Type load migration is narrowed to projects without `appVersion`. A fresh 2.10.7 browser round-trip remains a separate release-verification item. The rc12 source/CLI regression gate passes 324 tests, and all checked-in examples pass.

rc11 adds a normalized player-safe hierarchy to `play`. Visible Rows, direct Choices, and Addons are returned as separate entity lists with explicit parent/child IDs. This changes how an agent can inspect the player surface, but it does not weaken the visibility boundary. Hidden content and private runtime state remain excluded.

This package is an independent local command-line implementation. It does not bundle the ICC Plus browser application or claim that browser-only rendering, media playback, IndexedDB, screenshots, and modal behavior have been reproduced by the headless runner. The official Creator and Viewer remain the authority for final browser behavior and release verification.

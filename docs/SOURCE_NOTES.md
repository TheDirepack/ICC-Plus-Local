# Source notes

ICC Plus Local **0.10.0rc17** targets ICC Plus **2.10.16**, source commit `2bba0cf9ebc2e54241c2390794e95e1c5091b293` (October 30, 2026).

- Distribution: `wahaha303/ICCPlus` (official Viewer release v2.10.16).
- Creator and Viewer source: `wahaha303/ICC-Plus-Svelte`, pinned as above.
- Current Python headless source parity tests: 35 runtime sequences in the official Chromium Viewer, plus exact blank default export and TypeScript schema/required-field comparisons.
- The preceding 2.10.14 synchronization implemented protected Choices/selectable Addons and retained discount-refund Score state in sparse project saves.
- The 2.10.16 update fixes Build Form restoration of an allowed-to-deselect forced Choice; the previous 2.10.15 update addressed Viewer hosting/packaging for Neocities.
- Pinned Chromium parity: 94 gameplay cases, 57 action checkpoints, 12 sparse-equivalence cases with zero differences. The native discount subset includes one finite-use provider and up to three ordinary fixed nonnegative subtraction providers, with the source-verified stale full-price refund transition preserved through portable runtime state.

The field catalog and type metadata are checked against the pinned `types.ts`. The Viewer store and related components are used to audit game-state behavior. Creator source remains authoritative for authoring/import/export functionality and Svelte user-interface interactions.

The strongest returned external **Creator GUI** Save-to-Disk artifact is still the historical 2.10.6 C01 round-trip fixture. The pinned Chromium differential is an official **Viewer runtime** test, not a replacement for Creator GUI import/export validation. Dynamic discount stacks, separate omission probes, audio/media, site hosting and browser layout need their own coverage.

ICC Plus Local is an independent Python command-line tool; it does not ship a patched Svelte Viewer or implement hosting fixes itself. Use the official 2.10.16 Viewer distribution for Neocities deployment.

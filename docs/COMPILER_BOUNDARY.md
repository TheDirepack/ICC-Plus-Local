# ICC Plus Local compiler boundary

ICC Plus Local is the native ICC Plus compatibility, validation, serialization, and local-runtime layer. It should describe and reproduce ICC Plus behavior without silently redesigning a project.

Source-driven project optimization belongs in the compiler or lowering layer in front of ICC Plus Local. The compiler may simplify its own semantic source before emitting native ICC Plus operations, but ICC Plus Local should not infer or perform those transformations on arbitrary projects.

## ICC Plus Local owns

- ICC Plus version metadata and source-derived field/default behavior.
- Native project hydration and Creator-complete validation.
- Native Row, Choice, selectable-Addon, Requirement, Group, Score, Point, effect, and build-string semantics.
- Player-safe local simulation and deterministic regression support.
- Serialization, import/export, and reference-integrity checks.
- Viewer-runtime omission rules when absence is proven behavior-equivalent for the pinned target.
- Diagnostics for ambiguous or unsafe native states when they can be identified without guessing author intent.
- Explicit documentation of where local simulation is not browser or target-Viewer proof.

## The source compiler owns

- Removing redundant ancestor Requirements when the source dependency graph proves them unnecessary.
- Promoting identical child visibility gates to the owning Row when semantics are provably unchanged.
- Consolidating repeated styling into project scope, Design Groups, and Group-linked Design Group inheritance.
- Deciding whether source taxonomy becomes an ICC Plus runtime Group.
- Merging one-card Rows or otherwise changing physical Row layout.
- Inferring Pick 1 / Pick N intent from higher-level source and emitting the corresponding `allowedChoices` value.
- Deterministic runtime-ID compaction, complete reference remapping, reversible ID maps, and migration handling for already published IDs.
- Distinguishing semantic/test artifacts from compact release artifacts.

ICC Plus Local may validate the compiler's generated native project, but it must not make these project-design choices on the compiler's behalf.

## Important semantic boundaries

### Hidden Rows are not cleanup

A hidden Row controls visibility. It does not prove that already selected children were deselected. If a source compiler wants provider loss to invalidate child selections, it must emit an explicit native cleanup mechanism and test that behavior.

### `allowedChoices: 0` is unlimited

ICC Plus Local should preserve and simulate this native meaning. A compiler that knows a source Row is Pick 1 or Pick N should emit the intended positive maximum instead of expecting ICC Plus Local to infer it from presentation or sibling exclusions.

### Selectable Addons and ICC Plus 2.10.8

Upstream ICC Plus 2.10.8's changelog says that “Change choices per row could not change addons per row.” The corresponding source change is in width application: selectable Addons use `addonWidth`, while Rows and Choices use `objectWidth`. It is a layout-width fix, not evidence that `allowedChoices` selection limits changed.

Do not use the 2.10.8 changelog entry as justification for replacing tested selectable-Addon exclusion logic with Row selection limits. Any such replacement needs direct target-Viewer evidence for the actual mechanic.

### Creator-complete authoring versus sparse runtime serialization

Creator-eager/default fields are native authoring structure. Creator-complete projects, Creator Save-to-Disk output, and Creator-compatible exports should preserve the fields required for reliable Creator round-tripping.

The player-facing runtime payload is a different serialization target. ICC Plus Local may omit a native field there only when its absence is proven behavior-equivalent in the pinned Viewer. This is native serialization, not source-level normalization. Schema optionality, matching a Creator construction default, or saving bytes is not enough evidence on its own.

The default runtime serializer therefore strips the pinned 2.10.7 omission whitelist automatically while retaining unproven fields. Read `SPARSE_RUNTIME_SERIALIZATION.md` for the current rules and the generated browser-verification kit.

### Local simulation versus browser proof

The local simulator is a deterministic compatibility and regression tool. CSS/layout, browser presentation, and version-specific behaviors not covered by source-derived local parity remain target-Viewer responsibilities. Release claims should state which behaviors were proved locally and which were verified in the official Creator/Viewer.

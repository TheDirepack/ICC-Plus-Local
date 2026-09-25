# ICC Plus Local 0.10.0rc11 audit

Version 0.10.0rc11 improves the player-safe `play` surface without weakening its visibility boundary. The main change is a normalized visible hierarchy: Rows, direct Choices, and Addons are exposed as separate entity lists while the older nested Row/Choice representation remains available for compatibility.

Visible Rows now provide ordered `choice_ids`, selected direct Choices, currently available direct Choices, and deselectable direct Choices. Visible direct Choices provide their `row_id`, visible-order index, and Addon membership. Visible Addons provide their parent `choice_id`, `row_id`, and visible-order index. Top-level ordered ID lists make the currently visible structure cheap to inspect without traversing verbose nested data.

Selection availability is now explicit about entity type. New fields distinguish all selectable entities, direct Choices, and selectable Addons. The historical `available_choice_ids` and `deselectable_choice_ids` names remain as compatibility aliases with their previous behavior, including selectable Addons.

Multi-step `play` requests can now assert structural relationships with `row_choices` and `choice_rows`. These checks operate only on visible player data, so hidden and nonexistent IDs remain indistinguishable.

During the hierarchy work, the audit found a pre-existing parent-resolution defect for ordinary non-selectable Addons. `ProjectIndex.parent_choice()` accepted selectable Addons only, which meant informational Addons could be omitted from player views even when Viewer visibility rules exposed them. Parent resolution now covers both Addon kinds, with regression coverage for the normalized Addon surface.

Local regression for this candidate: 312 normal tests passed. The compression suite was intentionally not rerun for rc11. The new player-view behavior was also exercised against the active 5.6 MB CYOA project: after the initial Begin action, the compact player-safe view exposed four visible Rows and thirteen visible direct Choices with explicit parent Row IDs.

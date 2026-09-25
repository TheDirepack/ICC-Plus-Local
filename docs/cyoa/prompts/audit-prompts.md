# Reusable CYOA audit prompts

Replace bracketed placeholders before use. Each prompt is intended for a fresh review pass so one type of audit does not hide another.

## Semantic, structural, and rules audit

Audit the current CYOA at `[PROJECT]`.

First identify the actual current project version. Do not assume a conventional filename is newest when several build artifacts exist. State what you selected and why.

Read the project's authoring rules and `docs/audit-rules.md`. Audit the whole current project, including all rows or sections, choices, addons, requirements, groups, point effects, navigation records, optional modules, and player-facing helper content.

Check ownership, parent-child ordering, duplicate concepts, independent axes, navigation depth, title-description agreement, technical terminology, requirement-description agreement, point behavior, duplicate IDs, missing references, impossible requirements, contradictory requirements, and unreachable content.

Do not modify the project during this pass.

For every finding, include the stable IDs when available, evidence, why it violates a rule or creates a concrete problem, severity, and a short fix direction. Separate confirmed errors, structural refactors, lower-confidence design questions, and old issues that are confirmed fixed.

Finish with regression tests for the highest-risk repairs.

## Player-facing UX audit

Audit `[PROJECT]` from the player's point of view.

Use the approved player-safe interface for the player-facing pass. Start with a fresh state. After reproducing a visible problem, you may inspect the project to diagnose it if this audit is not required to remain blind. Keep the player-visible symptom separate from the implementation diagnosis.

Review labels, searchability, row order, scale order, navigation depth, locked-choice explanations, defaults, costs and refunds, required versus optional setup, generated controls, completion flow, and any implementation language exposed to the player.

Flag cases where a title makes sense only inside its parent but becomes ambiguous in global search. Flag choices whose important difference is buried in long text. Flag parent decisions that appear after detailed children.

Do not assume a local tool and the official Viewer have identical presentation. Mark uncertain parity issues and list the exact Viewer interaction that should be checked.

Do not edit the project. End with a Viewer regression checklist.

## Coverage audit

Audit `[PROJECT]` for important representational gaps.

Use the intended scope of the CYOA and the supplied stress-test targets. Ask whether each target can be represented through general systems rather than setting-specific one-off choices or unrelated approximations.

For every proposed addition, explain the broad problem it solves, which target classes need it, whether an existing system can be broadened or reorganized instead, and whether the feature belongs in core flow, an advanced branch, or a conditional branch.

Classify each finding as a true missing capability, an existing capability that is too narrow, an existing capability that is hidden or badly organized, an issue already covered by another general system, or unnecessary detail that should not be added.

Prefer a small number of reusable systems over a large list of special cases.

Do not edit the project.

## Prose and Unslop audit

Audit all player-facing prose in `[PROJECT]`.

Use an `unslop` skill or equivalent prose standard. Include row titles and descriptions, choice titles and descriptions, addons, navigation text, presets, helper text, repeat controls, optional-module text, and any provenance or debug text visible to players.

Look for vague attribution, generated-sounding filler, fancy wording where plain language is clearer, repetitive caveats, implementation-facing language, descriptions that only restate the title, descriptions too short to define the mechanic, descriptions so long that the important distinction is buried, inconsistent terminology, and loose wording that changes the mechanic.

Measure useful description-length statistics, but do not treat length alone as an error. Keep necessary technical precision.

Give representative rewrites for problems. Do not rewrite every clean description merely to make it different.

Do not edit the project unless explicitly asked.

## Title-description and selection-compatibility audit

Audit every row and choice in `[PROJECT]` for two linked problems.

First, compare each choice title with its description. Flag broader, narrower, or different meanings, weakened literal terms, scientific or legal labels used loosely, and descriptions that add independent capabilities not named in the title.

Second, inspect same-row selection logic. Check selection limits, positive and negative requirements, group requirements, generated repeat structures, and cleanup behavior. Find compatible choices that are incorrectly forced apart and contradictory choices that can coexist.

Do not assume an exclusion is broken merely because only one side contains the explicit negative requirement. Test the actual runtime behavior when the engine rechecks selected choices.

For a single-select row, verify that every choice answers the same question at the same level. Prefer splitting independent axes over simply enabling multi-select.

Keep uncertain design cases separate and state the decision the author must make before changing mechanics.

End with explicit regression combinations that should be accepted and combinations that should be rejected after repairs.

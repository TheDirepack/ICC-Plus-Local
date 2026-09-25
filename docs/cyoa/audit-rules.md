# Generic CYOA audit rules

Use these rules when reviewing an existing CYOA. Audit the current project, not an old report. Old reports are useful for regression history, but a previous finding is not evidence that the current version still has the problem.

## Audit the whole project

For a full audit, inspect all rows or sections, choices, addons or subchoices, requirements, groups, point effects, navigation records, optional modules, generated controls, and player-facing helper text. Sampling is useful for triage, not for a final correctness claim.

Separate confirmed errors from design questions. Record enough identifiers to reproduce each finding.

## Semantics

A title and description must define the same thing. Technical terms must keep their normal meanings. Literal quantitative words must remain literal. A description should state the selected capability or state rather than only listing consequences.

Flag choices that bundle independent axes without a clear reason. Flag choices that infer one property from an unrelated one. Flag player text that contains internal authoring, compiler, source, debug, or migration language.

A priced advantage should provide a meaningful benefit beyond the project's baseline, unless baseline configuration is intentionally priced across the whole system.

## Structure

Parents must appear before dependent children. Content must live under the domain that owns it. Major domains should not be interleaved without a reason. Navigation layers should add a real decision or useful grouping rather than another click.

Look for stranded rows, misplaced children, repeated one-to-one navigation, parent concepts placed beside their implementations, duplicate concepts, and unrelated questions forced into one row.

## Requirements and selection logic

Requirements must agree with descriptions. Check positive requirements, exclusions, group requirements, point thresholds, activation effects, visibility rules, selection limits, repeatable controls, and cleanup behavior after deselection.

Look in both directions. Some incompatible choices may be selectable together, while some compatible choices may be incorrectly forced apart.

For single-select rows, verify that all choices answer the same question at the same level. If they answer different questions, split the row instead of merely making it multi-select.

Check every referenced ID or group. Flag missing targets, impossible chains, circular dependencies, hidden prerequisites the player cannot discover, and forward dependencies that make the normal flow confusing.

## Economy

Verify starting balances, costs, refunds, repeatable scaling, discounts, grants, and affordability rules. The label shown to the player must match the sign and meaning of the mechanic.

Check whether ordinary required setup unexpectedly consumes a large share of the budget. Test several plausible builds, not only the cheapest or intended path.

## Player-facing UX

Audit the project as a first-time player. Look for unclear labels, duplicate visible titles, context-free names, scrambled scales, important controls hidden too deeply, advanced detail shown too early, unexplained locked choices, dead-looking sections, and completion requirements that are not visible.

Search should remain useful when a choice is viewed outside its parent context. A title such as `Size`, `Range`, or `Standard` may need qualification if the UI exposes global search.

Do not assume a local testing tool and the official Viewer render identically. Separate project problems from tool-parity questions and verify browser-only behavior in the real Viewer before release.

## Coverage

Ask whether the CYOA can represent broad classes of intended builds without one-off hacks. Prefer missing general systems over long lists of setting-specific omissions.

Classify coverage findings as one of these cases: a true missing capability, an existing capability that is too narrow, an existing capability that is hidden or badly organized, an issue already solved by another proposed general system, or unnecessary detail that should not be added.

## Prose

Use a consistent prose standard. For ordinary player-facing text, an `unslop` pass or equivalent can remove generated-sounding filler without changing meaning.

Flag vague claims, overly defensive caveats, implementation-facing wording, descriptions that only restate the title, descriptions that bury the important distinction, inconsistent game terms, and text that changes the mechanic through loose wording.

Do not rewrite clean text only to make it different. Repeated mechanical phrasing is often good.

## Content scope and gating

A UI content gate should not silently alter neutral in-world mechanics. Check that restricted material is gated appropriately and that neutral mechanics are not accidentally restricted because of where they are stored.

If age, lifecycle, legal status, spoilers, optional modules, or content ratings matter mechanically, require explicit rules for them rather than relying on folder placement or labels.

## Regression protocol

Every repair should have a concrete regression check. For structural changes, test navigation and reachability. For requirement changes, test one passing and one failing path. For economy changes, test point balances before and after selection and deselection. For repeatable choices, test increment, decrement, limits, save/load, and cleanup. For visibility changes, test both hidden and visible states.

Preserve IDs during ordinary repairs whenever possible. If an ID must change, treat the change as a migration and audit every reference.

## Finding format

For each finding, record the visible title, stable ID when available, category, severity, evidence, why the behavior is wrong or confusing, and the smallest safe fix direction. Keep implementation diagnosis separate from the player-visible symptom when both matter.

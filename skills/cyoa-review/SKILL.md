---
name: cyoa-review
description: Use when auditing CYOA design or implementation.
compatibility: Designed for CYOA plans and ICC Plus 2 projects, with /CYOA/cyoa-guide used when available.
---

# CYOA review

Review the project as both a player experience and an ICC Plus 2 implementation. Report concrete problems, their evidence, their effect, and the smallest useful fix.

Apply the external Unslop prose skill to replacement prose.

## Inputs

Load the plan or project, current working state, known invariants, relevant source material, and any existing test or release reports. Use `iccplus-local inspect`, `play`, and `project validate` when implementation evidence is needed; keep the review skill focused on judgment rather than duplicating those command workflows.

## Workflow

Review in this order:

1. Premise, player contract, non-goals, and completion rule.
2. Main format and rule clarity.
3. Section purpose, order, related-choice placement, and avoidable backtracking.
4. Choice quality, decision basis, consequences, and coverage.
5. Economy and complete sample builds.
6. Requirements, reachability, state, and implementation complexity.
7. Large-project normalization and unnecessary runtime duplication when relevant.
8. Source status, placeholders, terminology, and cross-section consistency.
9. Layout, accessibility, and mobile use.
10. Save, summary, static edition, and release expectations.

## Look for

- rules learned too late,
- choices with no useful decision basis or consequence,
- dominated or nearly mandatory options,
- painless drawbacks or fake budgets,
- dead currencies,
- duplicate section roles,
- hidden important content with no discoverability path,
- deep, circular, or unreachable requirements,
- ancestor navigation gates copied through every descendant,
- the same hide Requirement repeated on every Choice in a Row,
- `allowedChoices: 0` on Rows that are semantically Pick 1 or Pick N,
- pairwise sibling ID lists where an ordinary direct-Choice Row maximum would express the rule,
- one-card Rows that have no distinct gate, explanation, selection limit, or layout role,
- independent axes forced into one Row even though they need different limits,
- state duplicated unnecessarily in hidden variables,
- runtime Groups that exist only as authoring metadata and have no runtime consumer,
- private style or direct Design Group assignments repeated across large families instead of project style or Group-linked inheritance,
- generated release IDs that change nondeterministically between builds,
- compact release JSON being treated as editable source,
- hidden selected state incorrectly assumed to have been cleaned up,
- selectable Addon exclusivity relying on unverified Row-cap behavior for the target version,
- dense cards or unreadable grids,
- essential information conveyed only by color or images,
- incomplete build summaries,
- placeholders written as settled facts,
- source facts, inferences, and design choices mixed together,
- terminology drift,
- old ICC workarounds in current ICC Plus 2 content,
- generated output that no longer matches its authoritative source,
- authoring, debug, template, or placeholder metadata leaking into player-facing content.

For large source-driven projects, read `../../docs/cyoa/guide/21-large-project-normalization.md` before classifying duplication as necessary or wasteful.

## Output

Group findings by severity:

- **Blocking**: can produce illegal, broken, unreachable, or seriously misleading builds.
- **Important**: materially harms choice quality, clarity, balance, source accuracy, usability, or maintainability.
- **Minor**: worth cleaning up but does not change the core experience.

For every finding, include evidence, affected scope, impact, and a specific fix. Finish with representative complete builds or test paths when the format supports them.

For normalization findings, distinguish semantic problems from representation overhead. A large Creator-complete file is not automatically badly designed; some size comes from required/eager schema fields. Prefer evidence such as repeated equivalent Requirements, styles, Groups, IDs, or redundant Rows.

## Rules

- Do not rewrite the whole project only because another structure is possible.
- Distinguish confirmed defects from preferences.
- Separate source errors from design choices.
- Evaluate effective behavior at Row + Choice scope instead of requiring old physical Requirement placement.
- Treat visibility, availability, and cleanup as separate behaviors.
- Use technical guide files only for implementation issues found during review.
- Broaden sample builds when a large point-buy economy cannot be judged from a few examples.

## Final checks

- [ ] Every blocking or important finding has evidence.
- [ ] Findings identify affected scope and a concrete fix.
- [ ] Balance claims use complete builds where needed.
- [ ] Requirement findings include reachability or transition evidence where relevant.
- [ ] Normalization findings distinguish source semantics from generated representation.
- [ ] Source-status problems are separated from design problems.
- [ ] `references/review-checklist.md` is complete.

## References

Use the design sequence under `../../docs/cyoa/guide/`: `05-planning-a-cyoa.md`, `06-planning-templates.md`, `07-formats-and-rule-systems.md`, `08-structure-and-player-flow.md`, `09-writing-choices-and-content.md`, `10-research-ideation-and-images.md`, and `11-balance-and-playtesting.md`. Add the affected implementation file, `16-visual-design-and-responsive-layout.md`, and `21-large-project-normalization.md` when relevant.
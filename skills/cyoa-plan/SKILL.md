---
name: cyoa-plan
description: Use when planning a new CYOA or major redesign.
compatibility: Designed for ICC Plus 2 CYOAs and the /CYOA/cyoa-guide reference set when available.
---

# CYOA plan

Plan the player experience before creating large amounts of project data.

Apply the external Unslop skill to player-facing text written during planning.

## Inputs

Gather:

- premise and source boundaries,
- player goals and intended completion state,
- important content categories,
- known engine constraints,
- non-goals and unresolved questions.

## Workflow

1. Write the one-sentence premise, player contract, and non-goals.
2. Choose the main format and the simplest rule system that expresses the intended tradeoffs.
3. Build the complete section skeleton before long-form card writing.
4. Decide whether repeated content families need a source-side baseline-and-delta model; keep that inheritance in the authoring source, not in player-visible ICC Plus structure.
5. Make a coverage inventory for important choices. Record each role, niche, cost band, tradeoff, prerequisites, conflicts, and intended payoff.
6. Define the completion rule.
7. Define budgets, pick limits, free choices, drawbacks, prerequisites, exclusions, repeat purchases, and discounts only where the design needs them.
8. Order sections by information dependency and backtracking risk.
9. Decide how locked or hidden content is signaled to the player.
10. Define the minimum ICC Plus 2 state model. Prefer direct Choice Requirements over extra hidden state when both express the rule clearly.
11. Choose the public-ID policy.
12. Write a small representative set of choices to calibrate titles, description length, rule wording, cost notation, and image treatment.
13. Make several complete sample builds and broaden the sweep for large point-buy systems.
14. Write a test matrix for major gates, transitions, requirement paths, and completion rules.
15. Map the stable design to ICC Plus 2 entities, then hand implementation to `iccplus-local` rather than a separate create/edit wrapper skill.

## Rules

- Design the decision before the data model.
- Use the simplest rules that work.
- State what a legal finished build contains.
- Treat mandatory spending as part of the real budget.
- Avoid dominated choices and nearly mandatory options unless they are deliberate.
- Make drawbacks change the build or story, not only print points.
- Plan mobile layout while writing. Card density and prose length interact.
- Give important choices a decision basis and a consequence.
- Calibrate before bulk writing.
- Plan discoverability for important locked or hidden content.
- Keep source facts, supported inferences, design choices, and placeholders distinct.
- Plan save, Choice Import, Backpack, and summary behavior separately.
- Treat source-side templates, inheritance, and generation metadata as authoring machinery, not player-facing content.

## Output

Produce:

- premise, player contract, and non-goals,
- section skeleton and coverage inventory,
- completion rule and economy,
- state and ID policy,
- calibrated sample choices,
- representative full builds,
- test matrix,
- unresolved design or source questions.

## Final checks

- [ ] Premise, player contract, and non-goals are clear.
- [ ] Section skeleton, coverage, and order are defined.
- [ ] Completion rule is explicit.
- [ ] Economy and state model are defined.
- [ ] Important choices have a basis and intended consequence.
- [ ] Locked or hidden content has a discoverability policy.
- [ ] Representative choices were calibrated before bulk authoring.
- [ ] Several complete sample builds work on paper.
- [ ] Major gates and requirement paths have tests.
- [ ] `references/plan-checklist.md` is complete.

## References

Use `../../docs/cyoa/guide/05-planning-a-cyoa.md`, `07-formats-and-rule-systems.md`, `08-structure-and-player-flow.md`, `09-writing-choices-and-content.md`, `11-balance-and-playtesting.md`, `06-planning-templates.md`, `03-development-protocol.md`, and `10-research-ideation-and-images.md`.
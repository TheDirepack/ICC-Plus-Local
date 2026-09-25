# LLM development protocol

This file covers failure modes that become common when an LLM works on a CYOA across many passes.

The goal is not more process for its own sake. The goal is to stop local edits from quietly changing the project somewhere else.

## Keep a small working state

Before a substantial pass, load or reconstruct these items.

- Current project version.
- Player contract.
- Premise focus and non-goals.
- Section map.
- Point and selection rules.
- Mechanical invariants.
- Public ID policy.
- Style and terminology rules.
- Source boundaries.
- Open design decisions.
- Current test matrix.

For a long project, keep this in a short working file rather than relying on conversation memory.

## Keep one source of truth

If the project has structured source or a compiler, edit that source and regenerate the Viewer project. Treat generated `project.json` as disposable output, not a second editable master.

Keep reusable scripts under `/CYOA/tools/`. A revision folder can record which tool version or command produced an artifact, but it should not accumulate forked copies of the reusable generator or test harness.

When the local runner, local documentation, and target Viewer disagree, reduce the case and follow the target Viewer for project behavior. Update or limit the local model before continuing. Do not make the CYOA imitate a simulator bug.

## Label the status of claims

Source-based and fandom CYOAs need a clear boundary between research and invention.

Use these labels in private notes when useful.

- `engine fact`: verified behavior of the target ICC Plus 2 version.
- `source fact`: directly supported by the source material.
- `supported inference`: not explicit, but supported by several source details.
- `design choice`: invented for this CYOA.
- `placeholder`: temporary text or mechanics that still need a decision.

Do not turn a placeholder into an apparent fact by polishing its prose.

## Work in bounded passes

A pass should have a named scope such as "reprice the movement section" or "write the ten civilian technologies".

Before changing anything, state the rules and public IDs that must stay unchanged.

After the pass, record additions, edits, removals, tests, and unresolved issues. Do not silently delete older content because the new structure looks cleaner. Preserve useful material unless there is a reason to remove or merge it.

## Separate kinds of change

Do not combine a large balance pass, prose rewrite, layout redesign, and ID migration unless the task requires them together.

When possible, separate:

1. structural changes,
2. mechanical changes,
3. content additions,
4. prose cleanup,
5. visual changes.

This makes regressions easier to find.

## Use a content inventory

For medium and large sections, keep one row per planned choice.

Useful fields are:

- role or player fantasy,
- mechanical niche,
- cost band,
- weakness or tradeoff,
- prerequisite,
- conflict,
- later payoff,
- image brief,
- source status.

Generate against the inventory. Do not rely on the model to remember the entire option set while writing the next card.

## Calibrate before bulk generation

Write a small representative sample before generating a large family of similar options.

Use the sample to settle title style, description length, rules wording, cost notation, image ratio, and degree of detail. Then generate the rest against that pattern.

After bulk generation, compare the choices against each other. LLM output often drifts toward duplicated powers, repeated sentence shapes, inflated claims, and generic flavor.

## Preserve deliberate asymmetry

Not every section needs the same number of choices, identical prose length, or a perfectly even grid.

Do not add filler choices to make counts match. Do not flatten a deliberately unusual major option because most other cards follow a template.

Consistency should make the project easier to understand, not erase meaningful differences.

## Audit requirements as a graph

When a project has many prerequisites or hidden Rows, inspect the network rather than only individual gates.

Look for:

- orphaned content that cannot become visible,
- circular requirements,
- a path that depends on a choice hidden behind itself,
- long chains with no nearby explanation,
- requirements that become impossible after another forced state change,
- multiple gates that encode the same rule differently.

A passing test for one gate does not prove the whole path is reachable.

## Audit consequences

For each important choice, identify where its effect is visible.

The payoff can be immediate or delayed. It can change points, later availability, text, relationships, endings, or the player's imagined character. The important part is that the project does not repeatedly ask the player to make decisions that disappear without consequence.

For narrative branches that merge, keep callbacks or state differences so the merge does not erase the player's earlier choice.

## Protect vocabulary

Keep a glossary for recurring terms, currencies, units, ranks, factions, species, and mechanical verbs.

Use the same word for the same rule. Do not alternate between "credits", "points", and "budget" unless those are different things.

Search globally after a rename. A local prose edit can leave stale terms in requirements, summaries, help text, or later sections.

## Source discipline

When research is needed, search before filling a gap from memory. Prefer primary sources for factual claims where practical.

Keep source notes close enough that a later pass can tell why a claim exists. If evidence is incomplete, record the uncertainty instead of writing a confident invented explanation.

Do not copy source prose into player-facing text when a summary or original description will do.

## End every pass with two checks

First run the local checks for the changed section.

Then run a small global check for project invariants. Confirm the budget names, major completion rule, ID policy, section map, and source boundary still match the project.

A long project fails when every local edit is reasonable but the whole project slowly stops agreeing with itself.

## Preserve runtime state during continuing tests

When an LLM playtest continues across calls, use `iccplus-local play PROJECT --state FILE`. Keep that state file outside the player reasoning context.

For an ordered multi-action regression, pass a multi-step audit request to `play` and attach visible expectations to the steps. Do not reconstruct a continuing run from selected IDs and point totals.

Tie saved state to the project revision or fingerprint. After a project edit, start a new run unless cross-revision compatibility is the test.

When a long run exposes a bug, keep the private state for investigation and reduce the failure to the shortest player action sequence that still reproduces it.

## Use the player surface during scripted play

The LLM player should reason only from `play` output. Do not give it the complete raw project, hidden IDs, internal state ledgers, or compatibility-only diagnostic output.

Treat a rejected action as an invariant check. Record the semantic result and confirm that no partial state leaked from the failed attempt.

If a needed diagnostic is not part of the normal `play` surface, discover the current route with `reference commands` or the installed guide. Do not use retired `view`, `session`, or `state-check` commands from memory.
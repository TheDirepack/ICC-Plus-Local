# Planning a CYOA

Planning should answer design questions before they become hundreds of Rows and Choices.

## Start with the player contract

Write one short paragraph that tells the player what they are doing.

A strong contract answers these questions.

- Who or what is the player building, choosing, or deciding?
- What are the main limits?
- What does a finished build contain?
- Is optimization expected, optional, or beside the point?
- Is the goal roleplay, fantasy fulfillment, tactical tradeoffs, story setup, collection, or another experience?

Example:

> Build a licensed mage for a dangerous frontier expedition. Choose one origin, one training path, up to two companions, and any spells you can afford with 12 Arcana. Drawbacks can raise Arcana, but the final expedition threat must still be survivable by your build.

That paragraph already implies section types, a budget, limits, a drawback role, and a final test.

## Fix the premise before expanding it

Write the premise in one sentence and list a few non-goals. A non-goal is an attractive idea that does not belong in this project unless the premise changes.

When a new mechanic, setting element, or mode appears, name the section and player decision it improves. If it does not improve one, move it to an idea inbox for later instead of expanding the current CYOA by default.

This does not forbid hybrids. It makes each part justify its place in the same player experience.

## Decide the experience before the engine model

Do not begin with "I need ten Rows." Begin with the decisions the player should make.

For each intended decision, write four things.

- What question is the player answering?
- What makes two answers meaningfully different?
- Does the answer need a cost, pick limit, prerequisite, exclusion, or no mechanic at all?
- Does a later section depend on it?

If a section has no meaningful decision and only explains the setting, treat it as information rather than pretending it is a choice section.

## Choose the main format

Use `07-formats-and-rule-systems.md` to choose the main rules. Most long CYOAs are hybrids, but one mechanic should normally do most of the work.

Examples:

- Pick one origin, then use points for powers.
- Pick three traits from each category, with no global currency.
- Use one global budget for all benefits, with drawbacks adding points.
- Unlock later Rows through earlier identity choices.
- Build a base with separate budgets for staff, equipment, and defenses.

Avoid adding a second currency or another rule layer unless it creates a decision the first system cannot express cleanly.

## Make a section map

Plan the whole path before writing every option.

A section map should record:

- Section name.
- What the player decides there.
- Whether it is mandatory or optional.
- Currency or pick limit used.
- Inputs from earlier sections.
- Effects on later sections.
- Expected number of choices selected.
- Expected card density and text length.

This makes hidden dependencies visible early.

Build the full skeleton before polishing every card. A first-pass choice can be only a working title, one-line purpose, rough cost band, and prerequisite. Fill the structure first, then expand the choices that survive coverage and balance review.

For medium and large sections, keep a coverage table that records each important option's player fantasy, mechanical niche, cost band, tradeoff, closest competitor, and later payoff. This makes duplicate choices and missing roles easier to see before prose hides them.

## Plan authoring inheritance separately

Large repeated content families often benefit from source-side inheritance. Examples include a biological baseline shared by several species, a common equipment chassis with variants, or a faction template with local differences.

Use a baseline-and-delta model in the structured source when it removes duplication. Keep the baseline explicit, keep each override small, and make the compiler produce ordinary ICC Plus entities with all player-visible facts resolved.

Do not make the player infer inherited rules from an authoring template. Do not export inheritance controls, debug fields, or template names as player content. Treat source inheritance as a maintenance technique, not an ICC Plus mechanic.

## Plan section order around information needs

The best order is the one that minimizes unnecessary backtracking.

Ask what the player needs to know before spending a limited resource. If drawbacks materially change the main budget, either put them early enough to establish the budget or let the interface tolerate temporary overspending until the player reaches them. If a drawback only makes sense after seeing the benefits it gives up, put it later or cross-link it clearly.

The same rule applies to scenarios, enemies, companions, missions, and endings. Place a section before the decisions that require its information.

## Define completion

The project should know what a legal finished build looks like.

Examples:

- Exactly one body, one origin, and one destination, with nonnegative points.
- Any number of purchases, but at least one defense and one mobility option.
- Three gifts total, no points.
- One faction path and one ending, with mutually exclusive story branches.

A completion rule helps the LLM decide whether a Row needs an allowed-choice limit, a Requirement, a warning, or only prose.

## Plan optionality

Do not mark a section optional merely because it has no hard requirement. Decide whether skipping it is a supported play style.

An optional section should not secretly contain the only practical way to make the economy work unless that is intentional and explained.

## Plan state only when state is needed

Use state for behavior the player can observe or that the rules need.

Good uses include unlocking a faction path, tracking a toggle, recording a selected mode, changing a later description, or running a Button action.

Do not create hidden Variables and Points for facts that can be expressed directly by Choice Requirements. Extra state increases the number of states that can break.

## Plan IDs before implementation

Choose an ID policy before large-scale authoring. Semantic IDs are easier for an LLM to audit than random IDs in large projects.

Examples:

- `row_origin`
- `origin_cityborn`
- `point_arcana`
- `var_oath_broken`
- `req_can_enter_archive`

Do not encode current display order into IDs if sections may move.

## Plan with sample builds

Before implementation, make several complete builds on paper.

At minimum, test these when the format supports them.

- A straightforward expected build.
- A specialist build that spends heavily in one area.
- A broad generalist build.
- A drawback-heavy build if drawbacks fund purchases.
- A low-complexity build that skips optional systems.
- A build that tries to exploit discounts, repeated selection, or requirement interactions.

If only one sample build feels reasonable, the choice space may be narrower than it looks.

## Plan the implementation last

After the design works on paper, map it to ICC Plus 2.

- Rows for sections.
- Choices for selectable options.
- Addons for attached details or subchoices.
- Point Types for numeric pools.
- Scores for point changes.
- Requirements and Global Requirements for gates.
- Variables for action-driven state.
- Groups for set-based behavior.
- Design Groups for reusable native Row/Choice styling.
- Buttons for explicit player actions.
- Backpack and build save only when they improve the project.

The engine model should serve the design, not replace it.
## Recommended LLM planning output

When the user asks for a plan rather than direct implementation, return the design in this order unless another format is requested.

1. Premise, player contract, and non-goals.
2. Main format and why it fits.
3. Section map in play order.
4. Content coverage summary for important sections.
5. Rule and economy summary.
6. State and dependency summary.
7. Layout assumptions.
8. Sample builds.
9. Risks and open design decisions.
10. ICC Plus 2 implementation map.
11. Test matrix.

Separate a real open decision from a detail the LLM can choose safely. Do not fill the plan with questions whose answers can be inferred from the premise or established design.

# Common CYOA formats and rule systems

CYOAs use many rule patterns. A long project often mixes several, but each added system increases cognitive load.

## Pick one

The player selects exactly one option from a set.

Good for origins, species, starting locations, patrons, core classes, main scenarios, and mutually exclusive identities.

Use it when the choice is about direction rather than resource allocation.

Watch for false choices. If one option is clearly better in every relevant way, the section is not doing much work.

## Pick N

The player selects a fixed number of choices from a set.

Examples include pick three skills, choose two companions, or select five gifts.

This is easy to understand and avoids point arithmetic. It works best when choices are roughly comparable in scope. It works poorly when the same section mixes tiny conveniences with life-changing powers.

## Point-buy

The player receives a budget and spends it across priced choices.

Point-buy is useful when scope varies and the player should decide where to concentrate resources. It also supports expensive signature options and cheap supporting options.

Common failures include prices that do not create real tradeoffs, a budget so large that the player buys all desirable options, and many currencies that force constant accounting.

A point number is not meaningful by itself. Balance comes from the set of choices and the total budget.

## Per-section budgets

Each section has its own currency or pick limit.

This guarantees participation in selected sections and makes balancing local content easier. It reduces cross-section freedom.

Use it when each category represents a distinct resource or when the project needs every build to engage with certain categories.

Do not use separate currencies only to avoid balancing a shared budget. Too many isolated budgets can turn the CYOA into several unrelated checklists.

## Hybrid budget

A hybrid combines a global budget with local limits or free picks.

Examples:

- One free origin plus 20 points for everything else.
- Two free skills, then extra skills cost points.
- One companion slot plus points for upgrades.

Hybrids are common because they can protect important identity choices while preserving flexible spending.

Each special rule should be easy to state in one sentence. If the player needs a flowchart to understand basic purchasing, simplify it.

## Drawbacks for points

Drawbacks impose a cost on the fictional build and grant spending power.

Good drawbacks change how the build plays or how the story develops. A drawback that is irrelevant to the player's likely goals is free money.

Decide what role drawbacks have.

- Optional risk for a few extra purchases.
- A major part of character identity.
- A difficulty selector.
- A way to buy above the normal power ceiling.
- A scenario complication that creates new content.

Place drawbacks where the player can judge their value without excessive backtracking. Community preferences differ on exact placement because the right position depends on what the drawback affects.

## Perks and drawbacks as paired tradeoffs

A project can pair an advantage with a related cost instead of using a general drawback currency.

Examples include a powerful implant with maintenance needs, a patron with obligations, or a weapon with a dangerous side effect.

This often creates clearer fiction than a detached drawback bank.

## Prerequisite trees

Later choices require earlier choices.

Use trees when progression or specialization matters. Keep the visible path understandable. Deep chains can force the player to search backward through many sections.

A tree should usually communicate why the prerequisite exists. A power upgrade requiring the base power is intuitive. A perk requiring an unrelated choice only because of hidden balance math is harder to understand.

## Tiers and upgrades

A base choice has stronger levels or upgrades.

This works well for powers, equipment, facilities, and skills. ICC Plus 2 can implement tiers through separate Choices, Addons, multi-select counts, Requirements, or other supported mechanisms depending on the desired interaction.

Choose one representation and use it consistently within a section.

## Repeated purchase

A choice can be selected more than once or have a selectable quantity.

Use this for resources such as soldiers, rooms, charges, stat points, or repeated investments.

Repeated purchase adds runtime and balance complexity. Test score multiplication, discounts, refunds, Requirements, minimum and maximum counts, and save/load behavior.

## Mutually exclusive paths

Selecting one path blocks another.

Use this for factions, timelines, major classes, incompatible bodies, or story branches.

Exclusivity should match the fiction or a clear rule. Do not use it only to force replay value.

## Staged unlocks

Early choices reveal later Rows or Choices.

This can make a large project easier to read because the player sees only relevant content. It can also hide the true consequence of an early choice.

Use staged unlocks when later content genuinely depends on earlier state. Give the player enough information to understand that a path will narrow future options.

## Narrative branch

Choices change later scenes, events, or endings rather than mainly changing a numeric build.

A narrative CYOA can use little or no currency. Requirements, Variables, Words, Buttons, and hidden state may matter more than Point Types.

The main balance question becomes whether branches feel meaningfully different and whether the player can understand the consequences they are expected to predict.

## Builder or management CYOA

The player constructs a base, faction, ship, organization, settlement, team, or other system.

These often use several resource types because the fiction has separate constraints. Use multiple currencies only when each represents a real decision. A ship builder might justify mass, power, crew, and cost. A simple bedroom builder probably does not.

Builders benefit from a final summary that makes the whole configuration easy to review.

## Character builder

The player creates a person through identity, abilities, relationships, equipment, goals, and complications.

A common pattern is to make identity choices simple and spend most mechanical complexity on powers, skills, equipment, or drawbacks.

Do not assume every character builder needs species, class, perks, drawbacks, companions, gear, and a scenario. Include sections that serve the premise.

## Gift picker

The project presents a small or medium set of desirable options with light rules, often pick one, pick several, or a small budget.

The appeal comes from the choices themselves. Heavy state and prerequisite systems usually work against the format.

## Scenario or survival CYOA

The player prepares for a threat, journey, mission, apocalypse, tournament, or other test.

The scenario should appear early enough that the player understands what they are preparing for. If the threat is a surprise by design, the project must still give enough information for choices to feel fair.

## Questionnaire or identity result

The player answers questions and the project derives or reveals a result.

This differs from a normal build because the player may not be optimizing a budget. Variables, scores, hidden points, and result Rows can support this format.

Be clear about whether answers are meant to be honest preferences or strategic choices.

## Randomized format

Random rolls, random Buttons, or generated selections can constrain the build.

Randomness works when uncertainty is part of the premise. It is frustrating when it replaces choices the player expected to control.

Always decide whether rerolls are allowed and whether a saved build must preserve the random result.

## Choosing among formats

Prefer the simplest rule system that expresses the intended tradeoffs.

Ask these questions.

- Are options comparable enough for Pick N?
- Does the player need to trade one category against another?
- Does fiction justify separate budgets?
- Are prerequisites part of progression or only a balance patch?
- Will drawbacks create interesting builds or only more points?
- Does hidden state create a better experience than visible rules?

Do not add a mechanic only because another CYOA used it.

## Common rule to ICC Plus 2 mapping

This table is a planning shortcut. Query the current schema before implementation.

| Design rule | Common ICC Plus 2 building blocks |
| --- | --- |
| Pick exactly one | Row selection limit, mutually exclusive Choices, or Requirements when scope is wider than one Row |
| Pick up to N | Row allowed-choice controls |
| Global point-buy | Point Type plus Choice Scores |
| Per-section budget | Separate Point Type or local selection limit |
| Drawback grants points | Choice Score that increases the spending Point Type |
| Prerequisite | Choice or Row Requirement, or a reusable Global Requirement |
| Mutually exclusive paths | Requirements, deactivation actions, or separate gated Rows depending on the desired behavior |
| Upgrade tree | Base Choice plus dependent Choices or selectable Addons |
| Repeated purchase | Multi-select Choice with tested Score multiplication and limits |
| Hidden story flag | Variable when action-driven state is needed |
| Reusable named condition | Global Requirement |
| Set-wide behavior | Group |
| Shared local styling | Design Group |
| Dynamic player text | Word |
| Explicit state-changing action | Button or supported Choice function |
| Final build review | Backpack, result Rows, or another selected-choice summary |
| Return later | Build save |
| Share a build | Choice Import when its format fits the project |

Use the smallest combination that implements the rule. A Pick One section normally does not need a hidden Point Type, Variable, Group, and Button merely to enforce one selection.

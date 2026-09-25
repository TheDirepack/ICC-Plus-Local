# Planning templates

These templates are prompts for an LLM or worksheets for an author. Delete sections that do not apply.

## Template A. Small CYOA

Use for a gift picker, short scenario, short character concept, or other project with light mechanics.

```text
Title:
Premise:
Player contract:
Main format: Pick one / Pick N / small point-buy / other

Sections:
1.
2.
3.

For each section:
- Question the player answers:
- Selection rule:
- Number of options:
- Expected selections:
- Does anything later depend on it?

Completion rule:
Summary or Backpack needed? yes/no
Build save needed? yes/no
Mobile card layout:

Sample build 1:
Sample build 2:
Sample build 3:
```

## Template B. Point-buy character builder

```text
Title:
Premise:
Player contract:
Expected power level:
Expected finished build size:

Starting budget:
Budget name:
Can the budget go negative temporarily?
Can drawbacks add budget?
Expected drawback use:

Identity choices:
- Body/species:
- Origin/background:
- Faction/class/path:

Spending sections:
- Section:
  Typical cheap option:
  Typical medium option:
  Typical expensive option:
  Expected selections:

Drawbacks:
- Role in the project:
- Placement:
- Maximum or soft limit:

Prerequisite trees:
Mutual exclusions:
Repeated purchases:
Discounts:
Free picks:

Completion rule:
Build summary:
Save/import plan:

Sample builds:
1. Generalist
2. Specialist
3. Social or support
4. Drawback-heavy
5. Minimal-complexity

For each sample build record:
- Choices
- Total spend
- Drawbacks
- Points left
- Main strengths
- Main weaknesses
```

## Template C. Scenario or survival CYOA

```text
Scenario:
What the player knows before choosing:
Win or survival condition:
Failure conditions:

Player contract:
Preparation budget or pick limit:

Sections:
1. Starting situation
2. Body or role if relevant
3. Skills or powers
4. Equipment or resources
5. Allies
6. Complications or drawbacks
7. Mission plan or final choice

For every purchase, ask:
- What problem does this solve?
- Is that problem actually present in the scenario?
- Does another cheaper choice solve it better?

Test builds:
- Combat-heavy
- Mobility or escape
- Social or negotiation
- Resource-conservation
- High-risk high-reward
```

## Template D. Builder or management CYOA

```text
Thing being built:
Player role:
Goal:

Resources:
- Resource:
  Why it is separate:
  Starting amount:
  Main sinks:

Sections:
- Core chassis or location
- Capacity
- Staff or companions
- Systems or facilities
- Defense
- Mobility
- Quality-of-life
- Special projects
- Drawbacks or liabilities

Hard constraints:
Soft constraints:
Mutual exclusions:
Upgrade paths:
Repeated purchases:

Final summary must show:
- Major selected components
- Remaining resources
- Derived capacities or scores
- Any unresolved requirement
```

## Template E. Narrative branch

```text
Premise:
Player role:
What choices are in-character decisions rather than purchases?

State flags:
- Flag:
  What sets it:
  What reads it:

Branches:
- Branch name:
  Entry condition:
  Key scenes or Rows:
  Exit or ending:

Hidden information:
- What is hidden?
- Why is it hidden?
- Is the choice still fair without knowing it?

Endings:
- Ending:
  Required state:
  What earlier decisions it pays off:

Save behavior:
Replay behavior:
```

## Template F. ICC Plus 2 implementation map

Use after the design is stable.

```text
Project version:
Target ICC Plus 2 viewer version:

Point Types:
- id | name | start | integer/float | visible/hidden | purpose

Variables:
- id | default | changed by | read by | purpose

Words:
- id | default | changed by | purpose

Groups:
- id | members | feature using it

Design Groups:
- id | members | styling purpose

Global Requirements:
- id | plain-language rule | references

Rows:
- id | title | purpose | selection rule | visibility | layout

Choices:
- id | row | cost/scores | requirements | groups | addons | actions

Buttons:
- id/location | player label | actions | expected before/after state

Backpack:
Build save:
Choice Import:
Custom CSS:
External CSS:
Audio:
```

## Template G. Gate test table

```text
Gate:
Plain-language rule:
Attached to:

Case 1, minimum pass:
- Starting state:
- Action:
- Expected result:

Case 2, nearest fail:
- Starting state:
- Action:
- Expected result:

Case 3, state lost after activation:
- Starting state:
- Action:
- Expected result:

Case 4, save/load:
- Saved state:
- Expected loaded result:
```

## Template H. Design review

```text
Premise clear in the first screen? yes/no
Finished-build rule clear? yes/no
Main budget visible and understandable? yes/no
Section order causes avoidable backtracking? yes/no
Any mandatory-looking option? list
Any dominated option? list
Any dead currency? list
Any section players can skip without noticing? list
Any requirement hidden far from the affected choice? list
Any card too long for its layout? list
Any phone-only issue? list
Any old ICC behavior or workaround present? list

Three best sample builds:
1.
2.
3.

Three highest-risk mechanics:
1.
2.
3.
```


## Template I. Choice brief

Use before bulk-writing a large section.

```text
Choice working title:
Section:
Player fantasy or role:
Mechanical effect:
Cost or pick rule:
Main benefit:
Main limitation:
Closest competing choice:
Why a player might prefer this one:
Prerequisites:
Conflicts:
Later payoff or callback:
Image brief:
Source status: source fact / supported inference / original design / placeholder
Notes:
```

## Template J. Section coverage matrix

```text
Section:
Decision the section asks:

Required niches:
- niche:
- niche:

Choice | player fantasy | mechanical niche | cost band | weakness | closest competitor | distinct reason to pick
------ | -------------- | --------------- | --------- | -------- | ------------------ | -----------------------

Missing coverage:
Possible duplicates:
Choices that look mandatory:
Choices that look dead:
```

## Template K. LLM work pass

```text
Current version:
Bounded task for this pass:
Files or Rows in scope:
Player-facing rules that must not change:
Public IDs that must not change:
Sources in scope:
Open assumptions:

Changes made:
Additions:
Edits:
Removals:
Tests run:
Global consistency checks run:
New risks or open questions:
Next safe task:
```
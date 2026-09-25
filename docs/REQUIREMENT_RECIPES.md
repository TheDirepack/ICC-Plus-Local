# Requirement recipes

Requirements can be attached to Rows, Choices, Addons, Scores, Global Requirements, Sound Effects, and other Requirements.

Ordinary Requirements use the ICC Plus Creator's structural `id: ""` default. Do not assign project-wide IDs merely because the field exists.

## ID Requirement

Require a Choice, selectable Addon, or Variable to be active:

```json
{
  "type": "id",
  "required": true,
  "reqId": "origin_mage"
}
```

Require it to be inactive:

```json
{
  "type": "id",
  "required": false,
  "reqId": "origin_robot"
}
```

For a multiple-selection count, use the ICC Plus `/ON#N` suffix:

```json
{
  "type": "id",
  "required": true,
  "reqId": "stat_strength/ON#3"
}
```

The local generator's `requires` and `excludes` shortcuts create simple ID Requirements.

ICC Plus parses the numeric part of `/ON#N` with JavaScript `parseInt` behavior. A prefix such as `/ON#2junk` therefore reads as 2. Negative forced activation counts are effectively a no-op in the pinned 2.10.7 behavior. Preserve these quirks when reproducing source behavior.

## Point Requirement

```json
{
  "type": "points",
  "required": true,
  "reqId": "budget",
  "reqPoints": 5,
  "operator": "2"
}
```

Point comparison operators in the reviewed Viewer behavior are:

| Code | Meaning |
| --- | --- |
| `1` | `>` |
| `2` | `>=` |
| `3` | `==` |
| `4` | `<=` |
| `5` | `<` |
| `6` | `!=` |

## OR Requirement

Require at least two of three alternatives:

```json
{
  "type": "or",
  "required": true,
  "orNum": 2,
  "orRequireds": [
    {"type": "id", "required": true, "reqId": "skill_a"},
    {"type": "id", "required": true, "reqId": "skill_b"},
    {"type": "id", "required": true, "reqId": "skill_c"}
  ]
}
```

Nested Requirements also keep the source-compatible structural blank ID unless the upstream format gives that record a separate identity for another reason.

## Compare Point Types

`pointCompare` compares one Point Type against another Point Type or an arithmetic expression based on it.

```json
{
  "type": "pointCompare",
  "required": true,
  "reqId": "attack",
  "reqId1": "defense",
  "operator": "1",
  "more": [
    {"operator": "1", "points": 2, "priority": 1}
  ]
}
```

The example requires `attack > defense + 2`.

Arithmetic priority `0` is valid and must remain 0. Do not replace a falsy zero with the default priority.

Arithmetic `more[].operator` codes modeled from the Viewer logic are `1` add, `2` subtract, `3` multiply, `4` divide, and `5` modulo.

## Count selections in Groups

`selFromGroups` counts membership per requested Group. If one active Choice belongs to two requested Groups, it contributes twice. The Viewer does not deduplicate that Choice across the requested Group list.

```json
{
  "type": "selFromGroups",
  "required": true,
  "selGroups": ["group_magic"],
  "selNum": 2,
  "selFromOperators": "1"
}
```

## Count selections in Rows

```json
{
  "type": "selFromRows",
  "required": true,
  "selRows": ["row_skills", "row_perks"],
  "selNum": 3,
  "selFromOperators": "1"
}
```

## Count selections in the whole normal project

```json
{
  "type": "selFromWhole",
  "required": true,
  "selNum": 5,
  "selFromOperators": "1"
}
```

The selection-count comparator uses ICC Plus's own codes, which differ from Point Requirement operators. The local runtime models the reviewed Viewer behavior. For uncommon count rules, make passing and failing `play` audit cases rather than inferring the meaning from the numeric code.

## Global Requirement

```json
{
  "type": "gid",
  "required": true,
  "reqId": "greq_can_cast"
}
```

The referenced Global Requirement contains its own `requireds` array. The validator detects missing references and cycles.

## Word Requirement

```json
{
  "type": "word",
  "required": true,
  "reqId": "word_alignment",
  "orRequired": [
    {"req": "lawful"},
    {"req": "neutral"}
  ]
}
```

## Conditional Requirement participation

A Requirement can have its own `requireds` array. Those nested Requirements decide whether the parent Requirement participates in the enclosing Requirement list.

This is useful when one rule should apply only after another state exists. It is also easy to make confusing. Use a named Global Requirement if many objects need the same compound rule.

## Requirement display

Fields such as `showRequired`, `hideRequired`, `hideRequired2`, `beforeText`, `afterText`, and custom text control presentation of the rule. They do not replace the mechanical Requirement itself.

## Visibility

An unmet Row Requirement hides the Row in the reviewed Viewer.

An unmet Choice Requirement normally disables the Choice but does not hide it. To hide the Choice while unmet, use the requirement-state visibility filter. The local `hidden_until` and `gate` helpers set this correctly.

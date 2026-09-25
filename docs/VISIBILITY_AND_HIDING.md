# Visibility and hiding

ICC Plus has several mechanisms that can look similar in JSON but do different jobs. Keep them separate in scripts.

## Hide a Row until a prerequisite is met

Use a normal Row Requirement. The Viewer hides a Row whose Requirements fail.

```json
{
  "op": "gate",
  "source": "origin_mage",
  "targets": ["row_magic"]
}
```

## Hide a Choice until a prerequisite is met

A Choice needs both the Requirement and the requirement-state visibility filter.

Use `gate` for a hidden prerequisite or `require` when the Choice should stay visible but unavailable.

```json
{
  "op": "gate",
  "source": "school_fire",
  "target": "spell_fireball"
}
```

## Hide many existing objects behind one Choice

```json
{
  "op": "gate",
  "source": "path_magic",
  "targets": [
    "row_spells",
    "spell_fireball",
    "spell_ice",
    "spell_teleport"
  ]
}
```

`gate` is idempotent. `ungate` removes the simple gate and restores the Choice visibility setting by default.

## Hide parts of Choices after selecting a source Choice

This is the native "Hide the Contents of Choices" effect. It is not a prerequisite gate.

```json
{
  "op": "hide_contents",
  "source": "redaction_mode",
  "rows": ["row_results"],
  "contents": ["title", "image", "text", "score", "requirements"]
}
```

The Creator maps content types to these native codes:

| Name | Code |
| --- | --- |
| Choice title | `1` |
| Choice image | `2` |
| Choice text | `3` |
| Choice Score | `4` |
| Choice Requirement | `5` |
| Addon title | `6` |
| Addon image | `7` |
| Addon text | `8` |
| unselected Addon | `9` |
| unmet Addon | `10` |

The helper accepts readable names and writes the codes.

## Addon visibility

Addons have `requireds`, `showAddon`, and `hideAddon` behavior. Selectable Addons also have selection state. The exact visible result can depend on the parent Choice and Viewer settings such as showing all Addons.

Use normal Addon Requirements for simple gated Addons. Verify complex Addon presentation in the Viewer.

## Search and hidden choices

The reviewed Choice Viewer explicitly allows search rendering to bypass normal Choice visibility checks. Do not assume a Choice hidden in its normal Row is necessarily absent from every search-oriented view. Test search behavior in the target Viewer if secrecy matters.

## Testing visibility

The headless runner evaluates the Requirement state but does not render the DOM. For `hidden_until`, local tests can prove the gate condition while Viewer tests prove the final presentation.

For `hide_contents`, the local validator checks references and reports the advanced effect. Final visual behavior belongs in Viewer testing.

# Bulk selectors

Bulk selectors target a structural set without copying a long list of IDs. They use exact structural matching except for the documented literal case-insensitive substring filters.

## Preview before writing

Preview the exact selector with `inspect`:

```json
{
  "queries":[
    {
      "op":"match",
      "where":{"kind":"choice","row":"row_magic","id_prefix":"spell_"},
      "expect":12
    }
  ]
}
```

```bash
iccplus-local inspect project.json @inspect.json
```

The result includes the match count and matched entities. A failed `expect` is an error.

## Selector fields

Common fields include:

| Field | Meaning |
| --- | --- |
| `kind` | One exact entity kind. |
| `kinds` | Any listed entity kind. |
| `id` | One exact identity. |
| `ids` | Any listed identity. |
| `id_prefix` | IDs beginning with the string. |
| `row` / `rows` | Content in the named Row or Rows. |
| `parent` / `parents` | Direct children of the named parent or parents. |
| `group` / `groups` | Members of the named Group or Groups. |
| `title_contains` | Literal case-insensitive title substring. |
| `text_contains` | Literal case-insensitive text substring. |
| `path_prefix` | Indexed path prefix. |
| `backpack` | Backpack or normal project content. |

Fields are ANDed. Lists within one field are ORed.

## Use the same selector in the write

Put the unchanged selector in `where` and repeat the expected count:

```json
{
  "op":"effects",
  "where":{"kind":"choice","row":"row_implants","id_prefix":"implant_"},
  "expect":24,
  "effects":{"confirm":true}
}
```

Run that operation through the owning public phase command, here `rules`.

Use explicit refs instead when the target set is small, irregular, or hand-picked.

## Safety

A normal `structure`, `rules`, or `style` write runs on a copy and replaces the project only after its operation checks and final complete-project validation succeed. An expectation failure leaves the original file unchanged.

Re-preview after an earlier mutation that can change selector membership, order, names, Groups, or parentage.

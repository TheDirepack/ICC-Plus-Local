# CYOA skill authoring standard

Checked against the OpenAI skill documentation, the Agent Skills specification, and the rc12 CYOA routing model on 2026-09-25.

Authoritative references:

- OpenAI, Build skills: https://learn.chatgpt.com/docs/build-skills
- OpenAI Academy, Using skills: https://openai.com/academy/skills/
- Agent Skills specification: https://agentskills.io/specification

## Required format

Every skill lives in its own directory and contains `SKILL.md`.

`SKILL.md` starts with YAML frontmatter. The required fields are `name` and `description`.

The `name` must:

- use lowercase letters, digits, and hyphens only,
- be at most 64 characters,
- not start or end with a hyphen,
- not contain consecutive hyphens,
- exactly match the parent directory name.

The `description` must be non-empty and at most 1024 characters.

## Description rules

Descriptions control implicit routing.

For this project:

- start with `Use when`,
- front-load the main trigger terms,
- name the task or problem, not the workflow,
- avoid version numbers and implementation details,
- keep it to one short sentence at most,
- prefer 4 to 10 words and under about 80 characters,
- put exclusions and workflow detail in the skill body.

## Organization

Keep installable skill directories flat under `skills/`; do not create category folders around them.

Keep only skills that add a distinct reasoning or delivery job. Native ICC Plus 2 creation, editing, styling, media work, validation, and local testing belong to the single `iccplus-local` skill and its `functions/` guides.

The remaining high-level flow is `develop → plan → migrate if needed → iccplus-local → review → ship`. `cyoa-compress` remains only for exceptional external or legacy asset compression. `unslop` is a shared cross-project skill and lives only at the external Unslop skill.

Do not recreate `cyoa-create`, `cyoa-edit`, `cyoa-look`, or `cyoa-test`. Their old workflows are now covered by `iccplus-local`.

Keep per-skill details in that skill's `references/` folder. Put project-wide guide material in `../../docs/cyoa/guide/` and reusable executable tools in `../`. Do not copy a shared global skill into `skills/`; reference the external companion rather than copying it into this repository.

## Body rules

Keep each skill focused on one job.

Use this default shape when it fits:

1. short purpose statement,
2. inputs,
3. workflow,
4. rules,
5. output,
6. final checks,
7. references.

This structure is a local convention, not an Agent Skills requirement.

Write imperative steps with explicit inputs and outputs. Put large command references, parity lists, templates, and detailed technical notes in `references/`, tool documentation, or other on-demand files.

Keep `SKILL.md` below the Agent Skills 500-line limit. Prefer much shorter files for frequently loaded skills.

## Resources

Use:

- `references/` for detailed documentation loaded only when needed,
- `scripts/` for deterministic or repetitive executable work,
- `assets/` for reusable templates and static resources.

Reference files inside a skill with paths relative to the skill root.

Project-level documentation outside the skill directory may be referenced by its stable project path, such as `../../docs/cyoa/guide/...`.

## OpenAI metadata

OpenAI supports optional `agents/openai.yaml` for display metadata, invocation policy, and tool dependencies.

Do not put OpenAI-only invocation fields in `SKILL.md` frontmatter. For example, use:

```yaml
policy:
  allow_implicit_invocation: false
```

inside `agents/openai.yaml` when implicit invocation should be disabled.

## Version facts

Do not pin fast-changing tool versions, commits, artifact hashes, smoke-test hashes, or test counts in task skills.

Discover the installed tool at run time. Keep immutable release identity in release files, checksums, or release records.

## Testing

Test both routing and behavior.

Routing tests should include:

- prompts that must trigger the skill,
- prompts that must trigger a neighboring skill instead,
- ambiguous prompts that verify the boundary.

Behavior tests should check whether the skill causes the expected workflow and output shape.

`ROUTING-EVALS.md` is the current routing test set.
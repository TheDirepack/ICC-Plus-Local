# CYOA skill routing evals

Use these prompts after skill changes. The expected result is the primary skill that should own the task.

`iccplus-local` is the single implementation skill for native ICC Plus 2 work. Do not route creation, editing, visual work, or mechanical playtesting to separate wrapper skills.

Current bundled implementation: ICC Plus Local 0.10.0rc12 targeting ICC Plus 2.10.7.

`unslop` resolves from the single global copy at `/skills/unslop`.

| Prompt | Expected primary skill |
| --- | --- |
| "Plan the section order, point economy, and completion rules for a new ICC Plus CYOA." | `cyoa-plan` |
| "I have an approved plan. Add the new origin rows and choices." | `iccplus-local` |
| "Change the cost and requirement on these existing choices." | `iccplus-local` |
| "Make the cards readable on phones and assign final images." | `iccplus-local` |
| "Run boundary and stateful regression tests for the new requirement chain." | `iccplus-local` |
| "Audit this CYOA for dominated choices, dead currencies, and unreachable content." | `cyoa-review` |
| "This project came from old ICC and has custom legacy workarounds. Port it to ICC Plus 2." | `cyoa-migrate` |
| "Build the final offline Viewer package and test it exactly as delivered." | `cyoa-ship` |
| "Use the local CLI to inspect the project, update these rules, and run a player-safe audit." | `iccplus-local` |
| "This project will take many sessions across planning, authoring, testing, and visuals. Keep the work state coherent." | `cyoa-develop` |
| "Compress this old external release asset folder separately from the ICC Plus media workflow." | `cyoa-compress` |
| "Rewrite this paragraph so it sounds less AI-generated without changing its meaning." | global `unslop` |

## Boundary prompts

| Prompt | Expected result |
| --- | --- |
| "The plan is still unsettled. Should this section use points or pick limits?" | `cyoa-plan`, not `iccplus-local` |
| "The design is settled. Implement these rows, rules, and styles." | `iccplus-local`, not separate create/edit/look skills |
| "The project data looks clean. Prove repeated selection restores correctly after save/load." | `iccplus-local`, not a separate test skill |
| "Review the current CYOA for weak choices and balance problems. Do not change it yet." | `cyoa-review`, not `iccplus-local` |
| "The source is already ICC Plus 2. Fix a broken requirement." | `iccplus-local`, not `cyoa-migrate` |
| "The web build is done. Test the hosted URL and final asset loading." | `cyoa-ship`, not `iccplus-local` |
| "These images are being assigned through the normal ICC Plus media workflow. Make them efficient." | `iccplus-local`, not `cyoa-compress` |
| "Polish the prose, but leave code blocks and quoted source text unchanged." | global `unslop` |

## Removed skill names

These names are intentionally retired and must not be reintroduced as routing targets:

- `cyoa-create`
- `cyoa-edit`
- `cyoa-look`
- `cyoa-test`

Their ICC Plus operations belong to `iccplus-local`.
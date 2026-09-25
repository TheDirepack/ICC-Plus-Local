# Examples

Run the complete example suite from the repository root:

```bash
./examples/test_examples.sh
```

The files directly under `examples/` exercise the current rc11 canonical command surface against `demo_project.json`:

```bash
PYTHONPATH=. python -m iccplus_tools inspect examples/demo_project.json @examples/agent_inspect.json
PYTHONPATH=. python -m iccplus_tools structure examples/demo_project.json @examples/agent_operations.json --dry-run
PYTHONPATH=. python -m iccplus_tools structure examples/demo_project.json @examples/bulk_selector_ops.json --dry-run
PYTHONPATH=. python -m iccplus_tools rules examples/demo_project.json @examples/repair_ops.json --dry-run
PYTHONPATH=. python -m iccplus_tools style examples/demo_project.json @examples/visual_manifest.json --dry-run
PYTHONPATH=. python -m iccplus_tools play examples/demo_project.json @examples/demo_scenario.json
python examples/agent_automation.py
```

The two session request files demonstrate private continuation state. Run them in order against the same state file:

```bash
rm -f /tmp/iccplus-example-state.json
PYTHONPATH=. python -m iccplus_tools play examples/demo_project.json @examples/session_request.json --state /tmp/iccplus-example-state.json
PYTHONPATH=. python -m iccplus_tools play examples/demo_project.json @examples/session_continue_request.json --state /tmp/iccplus-example-state.json
```

Additional examples:

- `simple-cyoa/` is a small reproducible phased project with a player-safe smoke test.
- `main-cyoa-development/` is a standalone development excerpt derived from the current 6.6.11 main CYOA. It preserves real current content and IDs while omitting cross-section mechanics so the excerpt remains independent.

`visual_manifest.json` demonstrates the preferred style hierarchy: project-wide styling, a reusable official Choice Design Group, and a preset used only for repeated layout values. It does not duplicate shared styling into individual Choices.

The edit examples use `--dry-run` where appropriate so the checked-in fixtures are not modified by the test suite.

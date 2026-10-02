from __future__ import annotations

from iccplus_tools.simulator import Simulator


def choice(ident: str) -> dict:
    return {
        "id": ident,
        "index": 0,
        "title": ident,
        "text": "",
        "isActive": False,
        "multipleUseVariable": 0,
        "requireds": [],
        "scores": [],
        "addons": [],
        "groups": [],
    }


def id_requirement(ident: str) -> dict:
    return {
        "id": "",
        "required": True,
        "requireds": [],
        "orRequired": [],
        "orRequireds": [],
        "type": "id",
        "reqId": ident,
        "reqId1": "",
        "reqId2": "",
        "reqId3": "",
        "reqPoints": 0,
        "showRequired": False,
        "operator": "1",
        "afterText": "",
        "beforeText": "",
        "orNum": 1,
        "selNum": 1,
        "selFromOperators": "1",
        "more": [],
    }


def project(rows: list[dict]) -> dict:
    return {
        "version": "2.10.7",
        "defaultChoiceMaxNum": 99,
        "pointTypes": [],
        "variables": [],
        "words": [],
        "groups": [],
        "globalRequirements": [],
        "rows": rows,
        "backpack": [],
    }


def row(ident: str, *choices: dict, allowed: int = 0, requireds: list[dict] | None = None) -> dict:
    return {
        "id": ident,
        "index": 0,
        "title": ident,
        "titleText": "",
        "allowedChoices": allowed,
        "currentChoices": 0,
        "requireds": list(requireds or []),
        "objects": list(choices),
    }


def test_allowed_choices_zero_is_native_unlimited_selection():
    sim = Simulator(project([row("r", choice("a"), choice("b"), allowed=0)]))

    assert sim.select("a").ok
    assert sim.select("b").ok
    assert sim._active("a")
    assert sim._active("b")
    assert sim.state.row_counts["r"] == 2


def test_hidden_row_does_not_imply_cleanup_of_selected_children():
    sim = Simulator(
        project(
            [
                row("provider-row", choice("provider")),
                row("child-row", choice("child"), requireds=[id_requirement("provider")]),
            ]
        )
    )

    assert not sim.entity_visible("child")
    assert sim.select("provider").ok
    assert sim.entity_visible("child")
    assert sim.select("child").ok
    assert sim._active("child")

    assert sim.deselect("provider").ok
    assert not sim.entity_visible("child")
    assert sim._active("child")


def test_positive_allowed_choices_is_a_real_row_cap():
    sim = Simulator(project([row("r", choice("a"), choice("b"), allowed=1)]))

    assert sim.select("a").ok
    assert sim.select("b").ok
    assert not sim._active("a")
    assert sim._active("b")
    assert sim.state.row_counts["r"] == 1

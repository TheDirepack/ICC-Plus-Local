"""Viewer-card action tests grounded in ICC Plus 2.10.16 AppObject/ObjectAddon.

Only the click dispatcher is modeled here, not DOM/browser rendering.
"""
import copy
import json
import unittest
from pathlib import Path
from iccplus_tools.simulator import Simulator

DEMO = json.loads((Path(__file__).resolve().parents[1] / "examples" / "demo_project.json").read_text())


def make_project(*, once=False, multiple=False, allow_click=False, custom=False):
    project = copy.deepcopy(DEMO)
    row = project["rows"][0]
    row["allowedChoices"] = 1
    a, b = row["objects"][:2]
    row["objects"] = [a, b]
    a["id"], a["title"] = "preset_a", "A"
    b["id"], b["title"] = "preset_b", "B"
    for choice in row["objects"]:
        choice["requireds"] = []
        choice["scores"] = []
        choice["addons"] = []
        choice.pop("selectOnce", None)
        choice["isActive"] = False
    if once:
        a["selectOnce"] = True
    if multiple:
        a["isSelectableMultiple"] = True
        a["isMultipleUseVariable"] = True
        a["multipleUseVariable"] = 0
        a["numMultipleTimesPluss"] = 3
        a["allowSelectByClick"] = allow_click
    if custom:
        a["customTextfieldIsOn"] = True
        a["textfieldIsOn"] = True
        a["idOfTheTextfieldWord"] = "custom_word"
        a["wordChangeSelect"] = ""
        project["words"] = [{"id": "custom_word", "replaceText": ""}]
    return project


class ViewerCardClickTest(unittest.TestCase):
    def test_select_once_is_upstream_locked_not_simulator_bug(self):
        s = Simulator(make_project(once=True))
        self.assertTrue(s.click("preset_a").ok)
        e = s.click("preset_a")
        self.assertTrue(e.ok)
        self.assertEqual(e.code, "interaction.click_ignored")
        self.assertTrue(s._active("preset_a"))
        self.assertFalse(s.click("preset_b").ok)

    def test_reversible_row_capacity_switch(self):
        s = Simulator(make_project())
        self.assertTrue(s.click("preset_a").ok)
        self.assertTrue(s.click("preset_b").ok)
        self.assertFalse(s._active("preset_a"))
        self.assertTrue(s._active("preset_b"))
        self.assertTrue(s.click("preset_b").ok)
        self.assertFalse(s._active("preset_b"))

    def test_multi_card_noop_and_click_increment(self):
        s = Simulator(make_project(multiple=True, allow_click=False))
        self.assertEqual(s.click("preset_a").code, "interaction.click_ignored")
        s = Simulator(make_project(multiple=True, allow_click=True))
        self.assertTrue(s.click("preset_a").ok)
        self.assertEqual(s._count("preset_a"), 1)
        self.assertEqual(s.click("preset_a").code, "interaction.click_ignored")

    def test_active_word_click_edits_without_deselect(self):
        s = Simulator(make_project(custom=True))
        self.assertTrue(s.click("preset_a", word="Original").ok)
        self.assertTrue(s.click("preset_a", word="Revised").ok)
        self.assertTrue(s._active("preset_a"))
        self.assertEqual(s.state.custom_words["preset_a"], "Revised")
        self.assertIn("preset_a/WORD#Revised", s.export_build_string())

    def test_script_action_routes_click_and_ignores_locked_toggle(self):
        s = Simulator(make_project(once=True))
        out = s.apply_actions([
            {"action": "click", "id": "preset_a"},
            {"action": "click", "id": "preset_a"},
        ])
        self.assertEqual(len(out), 2)
        self.assertTrue(out[1]["event"]["details"]["ignored"])
        with self.assertRaises(ValueError):
            s.apply_actions([{"action": "click", "id": "preset_a", "unexpected": 1}])


if __name__ == "__main__":
    unittest.main()

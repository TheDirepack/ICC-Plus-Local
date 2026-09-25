from __future__ import annotations

import unittest

from iccplus_tools.field_catalog import FIELD_CATALOG
from iccplus_tools.field_types import (
    FIELD_TYPE_CODES,
    field_details,
    json_schema_for_kind,
    python_typeddicts,
    typescript_declarations,
    validate_field_value,
)


class FieldTypeTests(unittest.TestCase):
    def test_every_pinned_field_has_a_type(self):
        for kind, fields in FIELD_CATALOG.items():
            source_kind = 'row' if kind == 'backpack_row' else kind
            self.assertEqual(set(fields), set(FIELD_TYPE_CODES[source_kind]), kind)

    def test_source_types_catch_common_llm_mistakes(self):
        validate_field_value('choice', 'randomWeight', 2.5)
        validate_field_value('choice', 'discountRows', ['r1', 'r2'])
        validate_field_value('choice', 'isAutoActive', False)
        with self.assertRaisesRegex(ValueError, 'expects number'):
            validate_field_value('choice', 'randomWeight', '2.5')
        with self.assertRaisesRegex(ValueError, 'array of strings'):
            validate_field_value('choice', 'discountRows', 'r1')
        with self.assertRaisesRegex(ValueError, 'expects boolean'):
            validate_field_value('choice', 'isAutoActive', 0)

    def test_selectable_addon_discriminator_is_literal_true(self):
        validate_field_value('selectable_addon', 'isSelectable', True)
        with self.assertRaisesRegex(ValueError, 'literal true'):
            validate_field_value('selectable_addon', 'isSelectable', False)
        validate_field_value('addon', 'isSelectable', False)
        with self.assertRaisesRegex(ValueError, 'literal false'):
            validate_field_value('addon', 'isSelectable', True)

    def test_schema_is_strict_by_default_and_loose_on_request(self):
        strict = json_schema_for_kind('choice')
        loose = json_schema_for_kind('choice', additional_properties=True)
        self.assertFalse(strict['additionalProperties'])
        self.assertTrue(loose['additionalProperties'])
        self.assertEqual(strict['properties']['randomWeight'], {'type': 'number'})
        self.assertEqual(strict['properties']['discountRows']['items'], {'type': 'string'})

    def test_generated_interfaces_include_pinned_fields(self):
        ts = typescript_declarations(['choice'])
        py = python_typeddicts(['choice'])
        self.assertIn('export interface ChoicePatch', ts)
        self.assertIn('randomWeight?: number;', ts)
        self.assertIn('discountRows?: string[];', ts)
        self.assertIn('class ChoicePatch(TypedDict, total=False):', py)
        self.assertIn('randomWeight: float', py)
        self.assertIn('discountRows: list[str]', py)

    def test_details_include_upstream_default_when_exactly_known(self):
        detail = field_details('project', 'defaultChoiceTitle')
        self.assertEqual(detail['type'], 'string')
        self.assertIn('default', detail)


if __name__ == '__main__':
    unittest.main()

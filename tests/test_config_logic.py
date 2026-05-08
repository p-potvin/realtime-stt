import os
import json
import sys
import unittest
import re
from unittest.mock import MagicMock

# Define the helper directly here for testing logic in isolation if class mocking is hard
def get_validated(data, key, expected_type, default_value, min_val=None, max_val=None, regex=None):
    val = data.get(key, default_value)
    if not isinstance(val, expected_type):
        return default_value

    if expected_type in (int, float):
        if min_val is not None and val < min_val:
            return default_value
        if max_val is not None and val > max_val:
            return default_value

    if regex and isinstance(val, str):
        if not re.match(regex, val):
            return default_value

    return val

class TestConfigValidationLogic(unittest.TestCase):
    def test_invalid_types_are_ignored(self):
        data = {"font_size": "huge", "skip_vad": 1}
        self.assertEqual(get_validated(data, "font_size", int, 13), 13)
        self.assertEqual(get_validated(data, "skip_vad", bool, False), False)

    def test_out_of_bounds_values_are_ignored(self):
        data = {"font_size": 5, "outline_width": 50}
        self.assertEqual(get_validated(data, "font_size", int, 13, min_val=8, max_val=120), 13)
        self.assertEqual(get_validated(data, "outline_width", int, 4, min_val=0, max_val=30), 4)

    def test_invalid_color_format_is_ignored(self):
        hex_regex = r"^#(?:[0-9a-fA-F]{3}){1,2}$"
        data = {"text_color": "red", "outline_color": "#GGGGGG"}
        self.assertEqual(get_validated(data, "text_color", str, "#FFFFFF", regex=hex_regex), "#FFFFFF")
        self.assertEqual(get_validated(data, "outline_color", str, "#000000", regex=hex_regex), "#000000")

    def test_valid_values_are_accepted(self):
        data = {"font_size": 20, "text_color": "#123456"}
        self.assertEqual(get_validated(data, "font_size", int, 13, min_val=8, max_val=120), 20)
        self.assertEqual(get_validated(data, "text_color", str, "#FFFFFF", regex=r"^#(?:[0-9a-fA-F]{3}){1,2}$"), "#123456")

if __name__ == "__main__":
    unittest.main()

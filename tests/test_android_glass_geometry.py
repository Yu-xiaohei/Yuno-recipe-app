"""Pure regression checks for the clipped-semantics glass comparison defect."""

import copy
import unittest

from test_android_glass import surface_geometry


def navigation_fixture():
    return {
        0: {"cell": (202, 2072, 407, 2203), "icon": (273, 2085, 336, 2148),
            "label": (274, 2148, 336, 2190)},
        1: {"cell": (439, 2072, 643, 2203), "icon": (510, 2085, 573, 2148),
            "label": (510, 2148, 572, 2190)},
        2: {"cell": (675, 2072, 879, 2203), "icon": (746, 2085, 809, 2148),
            "label": (746, 2148, 808, 2190)},
    }


class GlassGeometryTests(unittest.TestCase):
    def test_full_surface_contains_labels_below_clipped_semantics(self):
        result = surface_geometry(navigation_fixture())
        self.assertEqual(result["bounds"], (170, 2069, 911, 2206))
        self.assertGreater(result["bounds"][3], 2146)
        self.assertEqual(result["densityFrom24dpIcon"], 2.625)
        self.assertEqual(result["minimumHeightPx"], 137)

    def test_json_keys_and_large_text_height_remain_supported(self):
        original = navigation_fixture()
        self.assertEqual(surface_geometry({str(key): value for key, value in original.items()}),
                         surface_geometry(original))
        enlarged = copy.deepcopy(original)
        for item in enlarged.values():
            left, top, right, _ = item["cell"]
            item["cell"] = (left, top, right, 2272)
        self.assertEqual(surface_geometry(enlarged)["bounds"], (170, 2072, 911, 2272))

    def test_changed_icon_contract_is_rejected(self):
        fixture = navigation_fixture()
        fixture[0]["icon"] = (273, 2085, 335, 2148)
        with self.assertRaisesRegex(AssertionError, "square"):
            surface_geometry(fixture)

    def test_inconsistent_layout_or_nonfinite_coordinates_are_rejected(self):
        fixture = navigation_fixture()
        fixture[1]["cell"] = (439, 2073, 643, 2203)
        with self.assertRaisesRegex(AssertionError, "vertical bounds"):
            surface_geometry(fixture)
        fixture[1]["cell"] = (439, float("nan"), 643, 2203)
        with self.assertRaisesRegex(AssertionError, "Non-finite"):
            surface_geometry(fixture)


if __name__ == "__main__":
    unittest.main()

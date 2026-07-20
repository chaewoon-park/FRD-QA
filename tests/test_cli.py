import copy
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from frdqa.cli import audit, check_catalog  # noqa: E402


class CatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = json.loads((ROOT / "src" / "frdqa" / "data" / "design-system-v1.6.json").read_text(encoding="utf-8"))
        cls.inventory = json.loads((ROOT / "examples" / "sample-inventory.json").read_text(encoding="utf-8"))

    def test_catalog_is_valid(self):
        self.assertEqual([], check_catalog(self.catalog))

    def test_sample_inventory_passes(self):
        self.assertFalse([item for item in audit(self.catalog, self.inventory) if item.level == "error"])

    def test_missing_review_is_reported(self):
        inventory = copy.deepcopy(self.inventory)
        inventory["components"][0]["reviewed"].remove("accessibility")
        codes = [item.code for item in audit(self.catalog, inventory)]
        self.assertIn("REVIEW_MISSING", codes)

    def test_unknown_type_is_reported(self):
        inventory = copy.deepcopy(self.inventory)
        inventory["components"][0]["implemented_types"] = ["invented"]
        codes = [item.code for item in audit(self.catalog, inventory)]
        self.assertIn("UNKNOWN_TYPE", codes)

    def test_missing_scope_record_is_reported(self):
        inventory = copy.deepcopy(self.inventory)
        inventory["components"].pop()
        codes = [item.code for item in audit(self.catalog, inventory)]
        self.assertIn("MISSING_IMPLEMENTATION", codes)


if __name__ == "__main__":
    unittest.main()

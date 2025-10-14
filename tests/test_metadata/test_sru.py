from unittest import TestCase
from src.ftva_etl.metadata.utils import _is_inventory_number_match


class TestInventoryNumberMatch(TestCase):
    def test_exact_match(self):
        self.assertTrue(_is_inventory_number_match("ABC", "ABC"))

    def test_no_match(self):
        self.assertFalse(_is_inventory_number_match("ABC", "DEF"))

    def test_prefix_with_suffix(self):
        self.assertTrue(_is_inventory_number_match("DVD123", "DVD123 T"))
        self.assertTrue(_is_inventory_number_match("VA456", "VA456 M"))
        self.assertTrue(_is_inventory_number_match("XFE789", "XFE789 R"))

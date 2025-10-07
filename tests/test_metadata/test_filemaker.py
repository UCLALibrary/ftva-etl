from unittest import TestCase
from src.ftva_etl.metadata.filemaker import (
    is_series_production_type,
)
from fmrest.record import Record


class TestFilemaker(TestCase):

    def setUp(self):
        valid_test_values = ["television series", "mini-series", "serials", "news"]
        self.valid_test_records = [
            Record(keys=["production_type"], values=[value])
            for value in valid_test_values
        ]

        invalid_test_values = ["foo", "bar", "baz", "buz"]
        self.invalid_test_records = [
            Record(keys=["production_type"], values=[value])
            for value in invalid_test_values
        ]

    def test_is_series_production_type(self):
        for record in self.valid_test_records:
            with self.subTest(record=record):
                self.assertTrue(is_series_production_type(record))

        for record in self.invalid_test_records:
            with self.subTest(record=record):
                self.assertFalse(is_series_production_type(record))

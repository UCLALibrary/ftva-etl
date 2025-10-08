from unittest import TestCase
from src.ftva_etl.metadata.filemaker import (
    is_series_production_type,
)
from fmrest.record import Record


class TestFilemaker(TestCase):
    def test_is_series_production_type(self):
        # Cherry-picked data from Filemaker PD that should be identified as series
        valid_test_cases = [
            "NEWS\rCOMPILATION",
            "TELEVISION SERIES\rCOMEDY",
            "MINI-SERIES\rDRAMA",
            "SERIALS\rACTION",
            " NEWS \rSHORT\r",
        ]
        # These should not be identified as series
        invalid_test_cases = [
            "SILENT FILM\rEDUCATIONAL\rNEWSREELS\rCARTOONS",
            "FOO\rBAR\rBAZ",
            "TELEVISION\rMINIATURE",
        ]
        self.valid_test_records = [
            # recordId and modId are added
            # for use in __repr__ method on Record class
            Record(
                keys=["recordId", "modId", "production_type"],
                values=[index, 0, value],
            )
            for index, value in enumerate(valid_test_cases)
        ]
        self.invalid_test_records = [
            Record(
                keys=["recordId", "modId", "production_type"],
                values=[index, 0, value],
            )
            for index, value in enumerate(invalid_test_cases)
        ]

        for record in self.valid_test_records:
            with self.subTest(record=record):
                self.assertTrue(is_series_production_type(record))

        for record in self.invalid_test_records:
            with self.subTest(record=record):
                self.assertFalse(is_series_production_type(record))

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


class TestFilemakerDateInfo(TestCase):
    def setUp(self):
        # Test cases are tuples, where 1st elem is input date info,
        # and 2nd elem is expected result from get_date_info()
        test_cases = [
            # Summary of specs:
            # - If release_broadcast_year is not empty, parse it as the release_broadcast_date;
            # - else if record_date is not empty, parse it as the production_date.
            # - If neither is present, return a dict with release_broadcast_date as an empty string.
            # - In all cases, release_broadcast_date should be present in the output dict,
            # but production_date should be present only if it is not empty.
            (
                {
                    "release_broadcast_year": "1997",
                    "record_date": "1997-12-02",
                },
                {"release_broadcast_date": "1997"},
            ),
            # only release_broadcast_year present
            (
                {"release_broadcast_year": "1997", "record_date": ""},
                {"release_broadcast_date": "1997"},
            ),
            # only record_date present
            (
                {"release_broadcast_year": "", "record_date": "11/9/2004"},
                {"release_broadcast_date": "", "production_date": "11/9/2004"},
            ),
        ]

        # Transform test cases into tuples of FM record and expected results
        self.test_records = [
            (
                Record(
                    keys=["recordId", "modId", "release_broadcast_year", "record_date"],
                    values=[
                        index,
                        0,
                        test_case[0]["release_broadcast_year"],
                        test_case[0]["record_date"],
                    ],
                ),
                test_case[1],  # expected result
            )
            for index, test_case in enumerate(test_cases)
        ]

    def test_get_date_info(self):
        """Test that `get_date_info` correctly extracts date info from FM records."""
        for record, expected_result in self.test_records:
            with self.subTest(record=record):
                self.assertDictEqual(get_date_info(record), expected_result)

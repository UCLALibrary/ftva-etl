from unittest import TestCase
from src.ftva_etl.metadata.filemaker import (
    is_series_production_type,
    get_date_info,
    get_title_info,
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
            # - If release_broadcast_year is not empty, map it to release_broadcast_date;
            # - else if record_date is not empty, map it to production_date.
            # - If neither is present, return an empty dict.
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
                {"production_date": "11/9/2004"},
            ),
            # neither present
            (
                {"release_broadcast_year": "", "record_date": ""},
                {},
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


class TestFilemakerTitleInfo(TestCase):

    def setUp(self):
        # Test cases are tuples, where 1st elem is input title info,
        # and 2nd elem is expected result from get_title_info().

        test_cases = [
            # Specs to test:
            # - If production type indicates compilation, return empty dict.
            # - If title is empty, return empty dict.
            # - If title is present and production type indicates a series,
            #   return a title, series title, and episode title (if present).
            # Compilation test cases:
            (
                {
                    "production_type": "compilation\rfoo\rbar",
                    "title": "Some Title 1",
                },
                {},
            ),
            (
                {
                    "production_type": "foo\rbar",
                    "title": "Contains a Compilation Keyword",
                },
                {},
            ),
            # Simple title test cases:
            (
                {
                    "production_type": "foo\rbar",
                    "title": "Some Title 2",
                },
                {"title": "Some Title 2"},
            ),
            (
                {
                    "production_type": "foo\rbar",
                    "title": "",
                },
                {},
            ),
            # Series title test cases:
            (
                {
                    "production_type": "television series\rfoo\rbar",
                    "title": "Series Title 1",
                    "ep_title": "Episode Title 1",
                    "ep_no": "Episode 1",
                },
                {
                    "title": "Series Title 1. Episode Title 1. Episode 1",
                    "series_title": "Series Title 1",
                    "episode_title": "Episode Title 1. Episode 1",
                },
            ),
            (
                {
                    "production_type": "television series\rfoo\rbar",
                    "title": "Series Title 2",
                    "ep_title": "",
                    "ep_no": "",
                },
                {"title": "Series Title 2"},
            ),
            (
                {
                    "production_type": "television series\rfoo\rbar",
                    "title": "Series Title 3",
                    "ep_title": "Episode Title 3",
                    "ep_no": "",
                },
                {
                    "title": "Series Title 3. Episode Title 3",
                    "series_title": "Series Title 3",
                    "episode_title": "Episode Title 3",
                },
            ),
            (
                {
                    "production_type": "television series\rfoo\rbar",
                    "title": "Series Title 4",
                    "ep_title": "",
                    "ep_no": "Episode 4",
                },
                {
                    "title": "Series Title 4. Episode 4",
                    "series_title": "Series Title 4",
                    "episode_title": "Episode 4",
                },
            ),
        ]
        self.test_records = [
            Record(
                keys=[
                    "recordId",
                    "inventory_id",  # added for use in logging in get_title_info()
                    "modId",
                    "production_type",
                    "title",
                    "ep_title",
                    "ep_no",
                ],
                values=[
                    index,
                    index,
                    0,
                    test_case[0]["production_type"],
                    test_case[0].get("title", ""),
                    test_case[0].get("ep_title", ""),
                    test_case[0].get("ep_no", ""),
                ],
            )
            for index, test_case in enumerate(test_cases)
        ]
        self.expected_results = [test_case[1] for test_case in test_cases]

    def test_get_title_info(self):
        """Test that `get_title_info` correctly extracts title info from FM records."""
        for record, expected_result in zip(self.test_records, self.expected_results):
            with self.subTest(record=record):
                self.assertDictEqual(
                    get_title_info(record, is_series_production_type(record)),
                    expected_result,
                )

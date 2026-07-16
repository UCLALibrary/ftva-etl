from unittest import TestCase
from src.ftva_etl.metadata.filemaker import (
    logger as fm_module_logger,
    is_series_production_type,
    get_date_info,
    get_title_info,
    get_file_path_info,
    get_creators,
    get_creation_date,
    get_media_type,
    get_audio_class,
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
                {"production_date": "2004-11-09"},
            ),
            # neither present
            (
                {"release_broadcast_year": "", "record_date": ""},
                {},
            ),
            # Value is `Unknown`
            (
                {"release_broadcast_year": "Unknown", "record_date": "Unknown"},
                {"release_broadcast_date": "Unknown"},
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
                    "episode_title": "Episode Title 1",
                    "episode no.": "Episode 1",
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
                    "episode_title": "",
                    "episode no.": "",
                },
                {"title": "Series Title 2"},
            ),
            (
                {
                    "production_type": "television series\rfoo\rbar",
                    "title": "Series Title 3",
                    "episode_title": "Episode Title 3",
                    "episode no.": "",
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
                    "episode_title": "",
                    "episode no.": "Episode 4",
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
                    "episode_title",
                    "episode no.",
                ],
                values=[
                    index,
                    index,
                    0,
                    test_case[0]["production_type"],
                    test_case[0].get("title", ""),
                    test_case[0].get("episode_title", ""),
                    test_case[0].get("episode no.", ""),
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


class TestFilemakerFilePathInfo(TestCase):
    def setUp(self):
        # Test cases are tuples, where 1st elem is input file path info,
        # and 2nd elem is expected result from get_file_path_info().
        test_cases = [
            (
                {
                    "file_path": "C:\\path\\to\\file.mp4",
                    "specific_carrier_type": "DCP",
                },
                {
                    "file_name": "",
                    "folder_name": "to",
                    "file_type": "DCP",
                },
            ),  # DCP test case
            (
                {
                    "file_path": "C:\\path\\to\\file.mp4",
                    "specific_carrier_type": "DPX",
                },
                {
                    "file_name": "",
                    "folder_name": "to",
                    "file_type": "DPX",
                },
            ),  # DPX test case
            (
                {
                    "file_path": "C:\\path\\to\\file.mp4",
                    "specific_carrier_type": "MOV",
                },
                {
                    "file_name": "file.mp4",
                },
            ),  # Non-DCP/DPX test case
            (
                {
                    "file_path": "/path/to/file.mov",
                    "specific_carrier_type": "MOV",
                },
                {
                    "file_name": "file.mov",
                },
            ),  # POSIX path test case
            (
                {
                    "file_path": "C:\\path\\to\\file.mp4",
                    "specific_carrier_type": "dcp",
                },
                {
                    "file_name": "",
                    "folder_name": "to",
                    "file_type": "DCP",
                },
            ),  # Lowercase DCP test case
        ]
        self.test_records = [
            Record(
                keys=["recordId", "modId", "file_path", "specific_carrier_type"],
                values=[
                    index,
                    0,
                    test_case[0]["file_path"],
                    test_case[0]["specific_carrier_type"],
                ],
            )
            for index, test_case in enumerate(test_cases)
        ]
        self.expected_results = [test_case[1] for test_case in test_cases]

    def test_get_file_path_info(self):
        """Test that `get_file_path_info` correctly extracts file path info from FM records."""
        for record, expected_result in zip(self.test_records, self.expected_results):
            with self.subTest(record=record):
                self.assertDictEqual(
                    get_file_path_info(record),
                    expected_result,
                )


class TestFilemakerCreators(TestCase):
    def setUp(self):
        test_cases = [
            # Comma-separated values are split and stripped
            (
                "Spielberg, Scorsese ,Coppola",
                ["Spielberg", "Scorsese", "Coppola"],
            ),
            # Non-comma value returned as a single-element list as-is
            (
                "Moss and Lewis ; Revue Studios ; Richard Lewis Productions.",
                ["Moss and Lewis ; Revue Studios ; Richard Lewis Productions."],
            ),
            (
                "Ford Beebe & Cliff Smith",
                ["Ford Beebe & Cliff Smith"],
            ),
        ]
        self.test_records = [
            (
                Record(
                    keys=["recordId", "modId", "director"],
                    values=[index, 0, director],
                ),
                expected,
            )
            for index, (director, expected) in enumerate(test_cases)
        ]

    def test_get_creators(self):
        """Test that `get_creators` splits comma-separated values
        and leaves values with other delimiters as-is.
        """
        for record, expected_result in self.test_records:
            with self.subTest(record=record):
                self.assertEqual(get_creators(record), expected_result)


class TestFilemakerCreationDate(TestCase):
    def test_get_creation_date_us_style(self):
        """Test that US-style dates are formatted as YYYY-MM-DD."""
        record = Record(
            keys=["recordId", "modId", "Creation_date"],
            values=[1, 0, "07/16/2026"],
        )
        self.assertEqual(get_creation_date(record), "2026-07-16")

    def test_invalid_creation_date_logs_and_raises(self):
        """Test that non-date values log an error then raise ValueError."""
        record = Record(
            keys=["recordId", "modId", "Creation_date"],
            values=[1, 0, "not-a-date"],
        )
        with self.assertLogs(fm_module_logger, level="ERROR") as log_context:
            with self.assertRaises(ValueError) as error_context:
                get_creation_date(record)
        expected_message = "Failed to parse creation date 'not-a-date' for record 1"
        # Assert that the error contains the expected message
        self.assertIn(expected_message, str(error_context.exception))
        # Assert that the logs contain the expected message
        self.assertIn(expected_message, log_context.output[0])


class TestFilemakerMediaType(TestCase):
    def test_get_media_type_allowlist(self):
        """Test that allowlisted media types are returned unchanged."""
        for media_type in ["Audio", "Image", "Video"]:
            with self.subTest(media_type=media_type):
                record = Record(
                    keys=["recordId", "modId", "media_type"],
                    values=[1, 0, media_type],
                )
                self.assertEqual(get_media_type(record), media_type)

    def test_invalid_media_type_logs_and_raises(self):
        """Test that non-allowlisted values log an error then raise ValueError."""
        for media_type in ["Film", ""]:
            with self.subTest(media_type=media_type):
                record = Record(
                    keys=["recordId", "modId", "media_type"],
                    values=[1, 0, media_type],
                )
                with self.assertLogs(fm_module_logger, level="ERROR") as log_context:
                    with self.assertRaises(ValueError) as error_context:
                        get_media_type(record)
                expected_message = f"Invalid media type '{media_type}' for record 1"
                # Assert that the error contains the expected message
                self.assertIn(expected_message, str(error_context.exception))
                # Assert that the logs contain the expected message
                self.assertIn(expected_message, log_context.output[0])


class TestFilemakerAudioClass(TestCase):
    def test_get_audio_class(self):
        """Test that empty audio_class maps to Unknown and non-empty values pass through."""
        test_cases = [
            ("", "Unknown"),
            ("Dialogue", "Dialogue"),
        ]
        for audio_class, expected in test_cases:
            with self.subTest(audio_class=audio_class):
                record = Record(
                    keys=["recordId", "modId", "audio_class"],
                    values=[1, 0, audio_class],
                )
                self.assertEqual(get_audio_class(record), expected)

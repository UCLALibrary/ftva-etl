import spacy
from unittest import TestCase
from src.ftva_etl.metadata.marc import (
    get_creators,
    get_date_info,
    get_language_name,
    get_title_info,
)
from pymarc import Record, Field, Indicators, Subfield


def _get_minimal_bib_record() -> Record:
    """Create a valid but minimal bib record with just 001 and 245 $a.
    This will be used as the base record, then copied & modified
    for other tests as needed.

    :return record: Minimal bib record with just 001 and 245 fields.
    """
    field_001 = Field(tag="001", data="12345")
    field_245 = Field(
        tag="245",
        indicators=Indicators("0", "0"),
        subfields=[Subfield(code="a", value="F245a")],
    )
    record = Record()
    record.add_field(field_001)
    record.add_field(field_245)
    return record


class TestMarcLanguagesRegion(TestCase):
    """Test the languages region of the MARC metadata module."""

    def setUp(self):
        self.minimal_bib_record = _get_minimal_bib_record()

    def _get_bib_record_bad_008(self) -> Record:
        """Create a bib record with an invalid 008 field,
        with bad data and incorrect length.

        :return record: Minimal bib record with a bad 008 field.
        """
        bad_field_008 = Field(tag="008", data="xxxxxxxxxxxxxxxx")
        record = self.minimal_bib_record
        record.add_field(bad_field_008)
        return record

    def test_get_language_name_no_008(self):
        # The minimal record has no 008 field.
        record = self.minimal_bib_record
        language_name = get_language_name(record)
        self.assertEqual(language_name, "")

    def test_get_language_name_bad_008(self):
        record = self._get_bib_record_bad_008()
        language_name = get_language_name(record)
        self.assertEqual(language_name, "")

    def test_get_language_name_invalid_code(self):
        # The minimal record has no 008 field; add one with an invalid
        # language code in positions 35-37.  Other data in the 008
        # does not matter for this, so use spaces.

        # A bib 008 field must have 40 characters.
        spaces = " " * 40
        # Set positions 35-37 to an invalid language code (not in the language map).
        field_008_data = spaces[:35] + "BAD" + spaces[38:]
        record = self.minimal_bib_record
        # Add the bad 008 field
        record.add_field(Field(tag="008", data=field_008_data))
        language_name = get_language_name(record)
        self.assertEqual(language_name, "")

    def test_get_language_name_valid_code(self):
        # The minimal record has no 008 field; add one with a valid
        # language code in positions 35-37.  Other data in the 008
        # does not matter for this, so use spaces.

        # A bib 008 field must have 40 characters.
        spaces = " " * 40
        # Set positions 35-37 to a valid language code (in the language map).
        field_008_data = spaces[:35] + "fre" + spaces[38:]
        record = self.minimal_bib_record
        # Add the good 008 field
        record.add_field(Field(tag="008", data=field_008_data))
        language_name = get_language_name(record)
        self.assertEqual(language_name, "French")


class TestMarcTitlesRegion(TestCase):
    """Test the titles region of the MARC metadata module."""

    def setUp(self):
        minimal_bib_record = _get_minimal_bib_record()
        # Remove the 245 field, so it can be explicitly added in each test.
        field_245 = minimal_bib_record.get("245")
        minimal_bib_record.remove_field(field_245)
        self.minimal_bib_record = minimal_bib_record

    def test_spec_case_1(self):
        """Test the spec case where the main title, name of part, and number of part are present."""
        record = self.minimal_bib_record
        record.add_field(
            Field(
                tag="245",
                indicators=Indicators("0", "0"),
                subfields=[
                    Subfield(code="a", value="Main Title"),
                    Subfield(code="p", value="Name of Part"),
                    Subfield(code="n", value="Number of Part"),
                ],
            )
        )
        titles = get_title_info(record)
        expected_result = {
            "title": "Main Title. Name of Part. Number of Part",
            "series_title": "Main Title",
            "episode_title": "Name of Part. Number of Part",
        }
        self.assertDictEqual(titles, expected_result)

    def test_spec_case_1_with_remainder_of_title(self):
        """Test the spec case where the main title, remainder of title,
        name of part, and number of part are present. This should be sufficient
        to cover the other cases as well, since this case includes all relevant title fields.
        """
        record = self.minimal_bib_record
        record.add_field(
            Field(
                tag="245",
                indicators=Indicators("0", "0"),
                subfields=[
                    Subfield(code="a", value="Main Title"),
                    Subfield(code="b", value="Remainder of Title"),
                    Subfield(code="p", value="Name of Part"),
                    Subfield(code="n", value="Number of Part"),
                ],
            )
        )
        titles = get_title_info(record)
        expected_result = {
            "title": "Main Title. Remainder of Title. Name of Part. Number of Part",
            "series_title": "Main Title. Remainder of Title",
            "episode_title": "Name of Part. Number of Part",
        }
        self.assertDictEqual(titles, expected_result)

    def test_spec_case_2(self):
        """Test the spec case where the main title and name of part are present,
        but the number of part is not.
        """
        record = self.minimal_bib_record
        record.add_field(
            Field(
                tag="245",
                indicators=Indicators("0", "0"),
                subfields=[
                    Subfield(code="a", value="Main Title"),
                    Subfield(code="p", value="Name of Part"),
                ],
            )
        )
        titles = get_title_info(record)
        expected_result = {
            "title": "Main Title. Name of Part",
            "series_title": "Main Title",
            "episode_title": "Name of Part",
        }
        self.assertDictEqual(titles, expected_result)

    def test_spec_case_3(self):
        """Test the spec case where the main title and number of part are present,
        but the name of part is not, and Filemaker indicates that the record is a series.
        """
        record = self.minimal_bib_record
        record.add_field(
            Field(
                tag="245",
                indicators=Indicators("0", "0"),
                subfields=[
                    Subfield(code="a", value="Main Title"),
                    Subfield(code="n", value="Number of Part"),
                ],
            )
        )
        titles = get_title_info(record, is_series=True)
        expected_result = {
            "title": "Main Title. Number of Part",
            "series_title": "Main Title",
            "episode_title": "Number of Part",
        }
        self.assertDictEqual(titles, expected_result)

    def test_spec_case_4(self):
        """Test the spec case where the main title and number of part are present,
        but the name of part is not, and Filemaker indicates that the record is not a series.
        """
        record = self.minimal_bib_record
        record.add_field(
            Field(
                tag="245",
                indicators=Indicators("0", "0"),
                subfields=[
                    Subfield(code="a", value="Main Title"),
                    Subfield(code="n", value="Number of Part"),
                ],
            )
        )
        titles = get_title_info(record, is_series=False)
        expected_result = {
            "title": "Main Title. Number of Part",
        }
        self.assertDictEqual(titles, expected_result)

    def test_spec_case_5(self):
        """Test the spec case where the main title is present,
        but the name of part and number of part are not.
        """
        record = self.minimal_bib_record
        record.add_field(
            Field(
                tag="245",
                indicators=Indicators("0", "0"),
                subfields=[
                    Subfield(code="a", value="Main Title"),
                ],
            )
        )
        titles = get_title_info(record)
        expected_result = {
            "title": "Main Title",
        }
        self.assertDictEqual(titles, expected_result)

    def test_error_condition_no_main_title(self):
        """Test the error condition where there is no main title."""
        record = self.minimal_bib_record
        record.add_field(
            Field(
                tag="245",
                indicators=Indicators("0", "0"),
            )
        )
        with self.assertRaises(ValueError):
            get_title_info(record)

    def test_error_condition_title_statement(self):
        """Test the error condition where there is no title statement."""
        record = Record()  # Totally empty record
        with self.assertRaises(ValueError):
            get_title_info(record)

    def test_trailing_punctuation(self):
        """Test trailing punctuation in the title elements."""
        record = self.minimal_bib_record
        record.add_field(
            Field(
                tag="245",
                indicators=Indicators("0", "0"),
                subfields=[
                    Subfield(code="a", value="Main Title /"),  # Trailing slash
                    Subfield(code="p", value="[Name of Part]"),  # Square brackets
                    Subfield(code="n", value="Number of Part . "),  # Trailing space
                ],
            )
        )
        titles = get_title_info(record)
        expected_result = {
            "title": "Main Title. Name of Part. Number of Part",
            "series_title": "Main Title",
            "episode_title": "Name of Part. Number of Part",
        }
        self.assertDictEqual(titles, expected_result)


class TestMarcDatesRegion(TestCase):
    """Test the dates region of the MARC metadata module."""

    def setUp(self):
        minimal_bib_record = _get_minimal_bib_record()
        self.minimal_bib_record = minimal_bib_record

    def test_no_date_field(self):
        record = self.minimal_bib_record
        date_info = get_date_info(record)
        expected_result = {"release_broadcast_date": ""}
        self.assertDictEqual(date_info, expected_result)

    def test_date_field_with_indicators(self):
        record = self.minimal_bib_record
        record.add_field(
            Field(
                tag="260",
                indicators=Indicators("1", "0"),  # Indicators not both blank
                subfields=[
                    Subfield(code="c", value="2023"),
                ],
            )
        )
        date_info = get_date_info(record)
        expected_result = {"release_broadcast_date": ""}
        self.assertDictEqual(date_info, expected_result)

    def test_date_field_260(self):
        record = self.minimal_bib_record
        record.add_field(
            Field(
                tag="260",
                indicators=Indicators(" ", " "),  # Both indicators blank
                subfields=[
                    Subfield(code="c", value="2023"),
                ],
            )
        )
        date_info = get_date_info(record)
        expected_result = {
            "release_broadcast_date": "2023",
        }
        self.assertDictEqual(date_info, expected_result)

    def test_date_260_priority_over_264(self):
        record = self.minimal_bib_record
        # Add a 264 field, which should be ignored if 260 is present
        record.add_field(
            Field(
                tag="264",
                indicators=Indicators(" ", "2"),
                subfields=[
                    Subfield(code="c", value="2022"),
                ],
            )
        )
        # Add the 260 field, which should take priority
        record.add_field(
            Field(
                tag="260",
                indicators=Indicators(" ", " "),
                subfields=[
                    Subfield(code="c", value="2023"),
                ],
            )
        )
        date_info = get_date_info(record)
        expected_result = {
            "release_broadcast_date": "2023",
        }
        self.assertDictEqual(date_info, expected_result)

    def test_date_264_first_indicator_not_blank(self):
        record = self.minimal_bib_record
        # Add a 264 field with first indicator not blank, which should be ignored
        record.add_field(
            Field(
                tag="264",
                indicators=Indicators("1", "2"),
                subfields=[
                    Subfield(code="c", value="2023"),
                ],
            )
        )
        date_info = get_date_info(record)
        expected_result = {
            "release_broadcast_date": "",
        }
        self.assertDictEqual(date_info, expected_result)

    def test_date_264_indicator_priority(self):
        record = self.minimal_bib_record
        # Add a 264 field with second indicator 2 (highest priority)
        record.add_field(
            Field(
                tag="264",
                indicators=Indicators(" ", "2"),
                subfields=[
                    Subfield(code="c", value="2023"),
                ],
            )
        )
        # Add a 264 with second indicator 1 (lower priority)
        record.add_field(
            Field(
                tag="264",
                indicators=Indicators(" ", "1"),
                subfields=[
                    Subfield(code="c", value="2022"),
                ],
            )
        )
        date_info = get_date_info(record)
        expected_result = {
            "distribution_date": "2023",
        }
        self.assertDictEqual(date_info, expected_result)

    def test_date_formatting(self):
        record = self.minimal_bib_record
        record.add_field(
            Field(
                tag="260",
                indicators=Indicators(" ", " "),
                subfields=[
                    Subfield(
                        code="c", value="[April 5, 2023]."
                    ),  # Brackets, period, and non-standard format
                ],
            )
        )
        date_info = get_date_info(record)
        expected_result = {
            "release_broadcast_date": "[2023-04-05]",
        }
        self.assertDictEqual(date_info, expected_result)

    def test_date_formatting_year_in_brackets(self):
        record = self.minimal_bib_record
        record.add_field(
            Field(
                tag="260",
                indicators=Indicators(" ", " "),
                subfields=[
                    Subfield(
                        code="c", value="[2023]"
                    ),  # Simple, four-digit year in brackets
                ],
            )
        )
        date_info = get_date_info(record)
        expected_result = {
            "release_broadcast_date": "[2023]",
        }
        self.assertDictEqual(date_info, expected_result)

    def test_date_formatting_year_in_brackets_with_hyphens(self):
        record = self.minimal_bib_record
        record.add_field(
            Field(
                tag="260",
                indicators=Indicators(" ", " "),
                subfields=[
                    Subfield(
                        code="c", value="[202-]"
                    ),  # Hyphen to indicate an uncertain year
                ],
            )
        )
        date_info = get_date_info(record)
        expected_result = {
            "release_broadcast_date": "[202-]",
        }
        self.assertDictEqual(date_info, expected_result)

    def test_date_field_008(self):
        record = self.minimal_bib_record
        # Add a 008 field with a date in position 7-10
        record.add_field(
            # 008 must be 40 characters
            Field(tag="008", data="xxxxxxx1970xxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
        )
        date_info = get_date_info(record)
        expected_result = {
            "release_broadcast_date": "1970",
        }
        self.assertDictEqual(date_info, expected_result)


class TestMarcCreatorsRegion(TestCase):
    """Test the creators region of the MARC metadata module.

    At present (2025-10-20), only directors should be included as creators.
    If this changes, tests will need to be revised.
    """

    def setUp(self):
        minimal_bib_record = _get_minimal_bib_record()
        # Minimal record has only 245 $a; add $c with multiple names in varied roles.
        f245 = minimal_bib_record.get("245")
        if f245:  # There is, but type-checker knows it *could* be None
            f245.add_subfield(
                code="c",
                value="director, John Director and Jessica Co-Director ; writer, Jane Writer.",
            )
        self.minimal_bib_record = minimal_bib_record

        # Needed for personal name parsing in get_creators
        self.nlp_model = spacy.load("en_core_web_md")

    def test_non_directors_are_excluded(self):
        record = self.minimal_bib_record
        creators = get_creators(record, self.nlp_model)
        self.assertNotIn("Jane Writer", creators)

    def test_directors_are_included(self):
        record = self.minimal_bib_record
        creators = get_creators(record, self.nlp_model)
        self.assertIn("John Director", creators)

    def test_multiple_directors_are_included(self):
        record = self.minimal_bib_record
        creators = get_creators(record, self.nlp_model)
        self.assertIn("Jessica Co-Director", creators)
        self.assertEqual(len(creators), 2)

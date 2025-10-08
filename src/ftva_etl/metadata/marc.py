import json
from importlib.resources import open_text
from pymarc import Record
from .utils import parse_date, strip_whitespace_and_punctuation

# for type hinting
from spacy.language import Language

# Code which extracts data from a NARC record.


# region Dates
def get_date(bib_record: Record) -> str:
    """Extract and format release_broadcast_date from a MARC bib record.

    :param bib_record: Pymarc Record object containing the bib data.
    :return: Formatted date string or an empty string if not found."""
    date_string = _get_date_from_bib(bib_record)
    if not date_string:
        return ""
    return parse_date(date_string)


def _get_date_from_bib(bib_record: Record) -> str:
    """Extract the release_broadcast_date from a MARC bib record.

    :param bib_record: Pymarc Record object containing the bib data.
    :return: Publication date as a string, or an empty string if not found."""
    # We want the first MARC 260 $c with both indicators blank.
    date_field = bib_record.get_fields("260")
    if date_field:
        for field in date_field:
            if field.indicator1 == " " and field.indicator2 == " ":
                date_subfield = field.get_subfields("c")
                if date_subfield:
                    return date_subfield[0].strip()
    # If no date found, return an empty string and log a warning.
    # TODO: LOGGING
    # logging.warning(f"No publication date found in bib record {bib_record['001']}.")
    return ""


# endregion


# region Creators
def _get_creator_info_from_bib(bib_record: Record) -> list:
    """Extract creators from the MARC bib record.

    :param bib_record: Pymarc Record object containing the bib data.
    :return: List of strings potentially containing creator names."""
    creators = []
    # MARC 245 $c is not repeatable, so we will always take the first one.
    marc_245_c = (
        bib_record.get_fields("245")[0].get_subfields("c")
        if bib_record.get_fields("245")
        else []
    )

    creators.extend(marc_245_c)
    return creators


def _parse_creators(source_string: str, model: Language) -> list:
    """Given a string sourced from MARC data, parse it to extract creator names.
    First, a list of attribution phrases is checked to see if the string
    contains any of them. If it does, the substring following the phrase
    is processed with a spacy NER model to extract names.

    :param source_string: String containing creator names from MARC data.
    :param model: Spacy language model for NER.
    :return: List of creator names."""

    # Initialize an empty string for the creator string
    creator_string = ""

    attribution_phrases = [
        "directed by",
        "director",  # This will also match "directors"
        "a film by",
        "supervised by",
    ]
    # Find location of the first attribution phrase
    for phrase in attribution_phrases:
        if phrase in source_string.lower():
            start_index = source_string.lower().find(phrase) + len(phrase)
            # Extract substring after the phrase until the end of the string
            # TODO: Does this work in general? Could a director be listed before
            # a non-director role that we shoudn't include?
            creator_string = source_string[start_index:].strip()
            break

    if not creator_string:
        return []

    doc = model(creator_string)
    creators = []
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            creators.append(ent.text)
    return creators


def get_creators(bib_record: Record, model: Language) -> list:
    """Extract and parse creator names from a MARC bib record.

    :param bib_record: Pymarc Record object containing the bib data.
    :param model: Spacy language model for NER.
    :return: List of parsed creator names."""
    creators = _get_creator_info_from_bib(bib_record)
    parsed_creators = []
    for creator in creators:
        parsed_creators.extend(_parse_creators(creator, model))
    return parsed_creators


# endregion


# region Languages
def _get_language_map(file_name: str = "language_map.json") -> dict:
    """Load the language map from a file.

    :param file_name: name of the language map file, with no extra path info.
    :return: Dictionary with language code:name data.
    """
    # importlib.resources.open_text() requires package path:
    # here, this is ftva_etl.metadata.data
    package_name = f"{__package__}.data"
    with open_text(package_name, file_name) as f:
        return json.load(f)


def _get_language_code_from_bib(bib_record: Record) -> str:
    """Extract the language code from a MARC bib record.

    :param bib_record: Pymarc Record object containing the bib data.
    :return language_code: The 3-letter MARC language code from the 008/35-37, or an empty string
    if there is no 008 or the 008 is invalid.
    """

    language_code = ""
    # 008 is not repeatable, so .get() instead of .get_fields().
    field_008 = bib_record.get("008")
    if field_008:
        field_data = field_008.data
        # MARC bib 008 should be 40 characters, or is not valid and can't be trusted
        # to have specific values in the correct positions.
        if field_data and len(field_data) == 40:
            # 3 characters, 0-based 35-37
            language_code = field_data[35:38]
    # TODO: LOGGING
    #     else:
    #         logging.warning(f"Invalid 008 field in bib record {bib_record['001']}")
    # else:
    #     logging.warning(f"No 008 field found in bib record {bib_record['001']}.")

    return language_code


def get_language_name(bib_record: Record) -> str:
    """Get the full name of the language in a MARC bib record.

    :param bib_record: Pymarc Record object containing the bib data.
    :param language_table: Dictionary which maps code:name for supported languages.
    :return language_name: The full name of the language.
    """

    # Load language mapping data.
    # TODO: should this be hard-coded? We'll only have 1;
    # regenerate it if missing?
    language_map = _get_language_map()

    language_code = _get_language_code_from_bib(bib_record)
    language_name = language_map.get(language_code, "")
    # TODO: LOGGING
    # if not language_name:
    #     logging.warning(
    #         f"No language name found in bib record {bib_record['001']} for {language_code}."
    #     )
    return language_name


# endregion


# region Titles
def get_title_info(bib_record: Record, is_series: bool = False) -> dict:
    """Extract title fields from a MARC bib record.

    :param bib_record: Pymarc Record object containing the bib data.
    :param is_series: Whether the record is a series, derived from Filemaker record.
    Defaults to False.
    :return: A dict with available title info.
    :raises ValueError: If no title statement (245 field) or main title (245$a) is found.
    """
    titles = {}
    record_id = get_record_id(bib_record)  # Used for ValueError messages

    title_statement = bib_record.get("245")
    if not title_statement:
        # No title statement (245 field) is an error condition, indicating an invalid record.
        # Raise a ValueError to be handled by callers.
        raise ValueError(f"No 245 field found in bib record {record_id}.")

    # Specs say to strip whitespace and punctuation from subfields,
    # then take first item if there are multiple.
    def _get_first_stripped(subfields: list[str]) -> str:
        stripped = strip_whitespace_and_punctuation(subfields)
        return stripped[0] if stripped else ""

    main_title = _get_first_stripped(title_statement.get_subfields("a"))
    name_of_part = _get_first_stripped(title_statement.get_subfields("p"))
    number_of_part = _get_first_stripped(title_statement.get_subfields("n"))

    # Handling the spec cases in reverse order,
    # to fail early and go from simplest to most complicated.
    # CASE 6: No main title
    if not main_title:
        # No main title (245 $a) is an error condition, indicating an invalid record.
        # Raise a ValueError to be handled by callers.
        raise ValueError(f"No 245 $a found in bib record {record_id}.")

    # CASE 5: Main title, but no name of part or number of part
    if main_title and not name_of_part and not number_of_part:
        titles["title"] = main_title

    # CASE 4: Main title and number of part, but no name of part (for non-series)
    if not is_series and main_title and number_of_part and not name_of_part:
        titles["title"] = ". ".join([main_title, number_of_part])

    # CASE 3: Main title and number of part, but no name of part (for series)
    if is_series and main_title and number_of_part and not name_of_part:
        titles["title"] = ". ".join([main_title, number_of_part])
        titles["series_title"] = main_title
        titles["episode_title"] = number_of_part

    # CASE 2: Main title and name of part, but no number of part
    if main_title and name_of_part and not number_of_part:
        titles["title"] = ". ".join([main_title, name_of_part])
        titles["series_title"] = main_title
        titles["episode_title"] = name_of_part

    # CASE 1: Main title, name of part, and number of part
    if main_title and name_of_part and number_of_part:
        titles["title"] = ". ".join([main_title, name_of_part, number_of_part])
        titles["series_title"] = main_title
        titles["episode_title"] = ". ".join([name_of_part, number_of_part])

    return titles


# endregion


# region Record IDs
def get_record_id(marc_record: Record) -> str:
    """Extract the record id from the MARC record. Applies to
    any type of MARC record, since all should have this in 001 field.

    :param marc_record: Pymarc Record object
    :return record_id: The MARC record id.
    """
    field_001 = marc_record.get("001")
    return field_001.value() if field_001 else ""


def get_bib_id(marc_record: Record) -> str:
    """Wrapper for get_record_id, in case callers need to work with both
    bibliographic and holdings MARC records.

    :param marc_record: Pymarc Record object
    :return record_id: The MARC record id.
    """
    return get_record_id(marc_record)


# endregion

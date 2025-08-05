import json
from pymarc import Record
from .utils import parse_date, strip_whitespace_and_punctuation

# for type hinting
from spacy.language import Language


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


def _get_language_map(file_path: str) -> dict:
    """Load the language map from a file.

    :param file_path: Path to the language map file.
    :return: Dictionary with language code:name data.
    """
    with open(file_path, "r") as file:
        return json.load(file)


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
    language_map = _get_language_map("../data/language_map.json")

    language_code = _get_language_code_from_bib(bib_record)
    language_name = language_map.get(language_code, "")
    # TODO: LOGGING
    # if not language_name:
    #     logging.warning(
    #         f"No language name found in bib record {bib_record['001']} for {language_code}."
    #     )
    return language_name


def _get_main_title_from_bib(bib_record: Record) -> str:
    """Extract the main title from a MARC bib record.

    :param bib_record: Pymarc Record object containing the bib data.
    :return: Main title string, or an empty string if not found.
    """
    title_field = bib_record.get("245")
    if title_field:
        main_title = title_field.get("a")  # 245 $a is NR, so take first item
        if main_title:
            return main_title
    # TODO: LOGGING
    # If no main title found, log a warning and return an empty string.
    # logging.warning(f"No main title (245 $a) found in bib record {bib_record['001']}.")
    return ""


def _get_alternative_titles_from_bib(bib_record: Record) -> list[str]:
    """Extract alternative titles from a MARC bib record.

    :param bib_record: Pymarc Record object containing the bib data.
    :return: A list of alternative titles, or an empty list if none found.
    """
    alternative_titles = []
    alternative_titles_field = bib_record.get_fields("246")
    for field in alternative_titles_field:
        # Per specs, only take 246 $a if indicator1 is 0, 2, or 3 and indicator2 is empty
        if field.indicator1 in ["0", "2", "3"] and field.indicator2 == " ":
            alternative_titles += field.get_subfields("a")
    return alternative_titles


def _get_series_title_from_bib(bib_record: Record, main_title: str) -> str:
    """Determine if record describes series, and return main title as series title if so.

    :param bib_record: Pymarc Record object containing the bib data.
    :return: The series title string, or an empty string.
    """
    title_field = bib_record.get("245")
    if title_field:
        number_of_part = title_field.get_subfields("n")
        name_of_part = title_field.get_subfields("p")
        if number_of_part or name_of_part:
            return main_title  # series title is main title if 245 $n or 245 $p exist
    return ""


def _get_episode_title_from_bib(bib_record: Record) -> str:
    """Extract and format episode title from a MARC bib record.

    :param bib_record: Pymarc Record object containing the bib data.
    :return: The episode title, formatted according to specs, or an empty string.
    """
    name_of_part = []  # Init to avoid being potentially unbound
    number_of_part = []
    title_field = bib_record.get("245")
    if title_field:
        name_of_part = title_field.get_subfields("p")
        if name_of_part:
            # Per specs, if there are multiple 245 $p, take the first one.
            # Assign it as a list though, so it can be easily joined with other lists.
            # Specs say episode titles specifically
            # should be stripped of whitespace and punctuation.
            name_of_part = [strip_whitespace_and_punctuation(name_of_part)[0]]

        number_of_part = strip_whitespace_and_punctuation(
            title_field.get_subfields("n")
        )

    alternative_number_of_part = []
    alternative_titles_field = bib_record.get_fields("246")
    if alternative_titles_field:
        for field in alternative_titles_field:
            alternative_number_of_part += strip_whitespace_and_punctuation(
                field.get_subfields("n")
            )

    if name_of_part or number_of_part or alternative_number_of_part:
        return ". ".join(name_of_part + number_of_part + alternative_number_of_part)
    return ""


def get_title_info(bib_record: Record) -> dict:
    """Extract title fields from a MARC bib record.

    :param bib_record: Pymarc Record object containing the bib data.
    :return: A dict with available title info.
    """
    titles = {}

    main_title = _get_main_title_from_bib(bib_record)
    alternative_titles = _get_alternative_titles_from_bib(bib_record)
    series_title = _get_series_title_from_bib(bib_record, main_title)
    episode_title = _get_episode_title_from_bib(bib_record)

    # Alternative titles are independent of the others.
    if alternative_titles:
        titles["alternative_titles"] = alternative_titles

    # The unqualified title ("title") depends on others.
    if series_title and episode_title:
        # Concatenate them with just a space, since series title
        # ends with punctuation (usually... possible refinement later).
        titles["title"] = f"{series_title} {episode_title}"
    else:
        titles["title"] = main_title

    if series_title:
        titles["series_title"] = series_title

    if episode_title:
        titles["episode_title"] = episode_title

    return titles


def get_record_id(marc_record: Record) -> str:
    """Extract the record id from the MARC record. Applies to
    any type of MARC record, since all should have this in 001 field.

    :param marc_record: Pymarc Record object
    :return record_id: The MARC record id.
    """
    field_001 = marc_record.get("001")
    return field_001.value() if field_001 else ""

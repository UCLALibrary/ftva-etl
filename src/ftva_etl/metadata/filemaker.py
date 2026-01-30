from fmrest.record import Record
from .utils import cleanup_production_type

# Code which extracts data from a Filemaker record.
# Minimal for now.


def get_inventory_id(fm_record: Record) -> str:
    """Get the inventory id from a Filemaker record.

    :param fm_record: A Filemaker record.
    :return: The inventory id as a string.
    """
    return str(fm_record.inventory_id)


def get_inventory_number(fm_record: Record) -> str:
    """Get the inventory number from a Filemaker record.

    :param fm_record: A Filemaker record.
    :return: The inventory number as a string.
    """
    return fm_record.inventory_no


def is_series_production_type(fm_record: Record) -> bool:
    """Determine if the `production_type` field represents a series,
    based on certain keywords defined in FTVA specs.

    :param fm_record: A Filemaker record.
    :return: True if the production type is a series, False otherwise.
    """

    production_type = cleanup_production_type(fm_record.production_type)
    series_keywords = ["television series", "mini-series", "serials", "news"]
    # Look for any of the keywords in the production type list
    return any(keyword in production_type for keyword in series_keywords)


def get_creators(fm_record: Record) -> list:
    """Get the creators from a Filemaker record.

    :param fm_record: A Filemaker record.
    :return: A list of creators.
    """
    # Currently splitting on commas,
    # as that appears to be how the data is formatted in Filemaker.
    # If other delimiters are used, they should probably be made consistent on the FM side.
    return [creator.strip() for creator in fm_record.director.split(",")]


def get_language_name(fm_record: Record) -> str:
    """Get the language name from a Filemaker record.

    :param fm_record: A Filemaker record.
    :return: The language name as a string.
    """
    # NOTE: field name is capitalized in FM
    return fm_record.Language


def get_date_info(fm_record: Record) -> dict:
    """Get the date info from a Filemaker record.

    :param fm_record: A Filemaker record.
    :return: A dict containing the date info.
    """
    # If FM data has `release_broadcast_year`, map it to `release_broadcast_date`.
    # Else, if FM data has `record_date`, map it to `production_date`.
    # Else, return an empty dict.
    # NOTE: we're taking values as-is from FM here,
    # mapping them to the date-like keys in the MAMS metadata.
    date_info = {}

    if fm_record.release_broadcast_year.strip() != "":
        date_info["release_broadcast_date"] = fm_record.release_broadcast_year
    elif fm_record.record_date.strip() != "":
        date_info["production_date"] = fm_record.record_date

    return date_info

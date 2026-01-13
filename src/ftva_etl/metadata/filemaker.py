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
    # Might need to handle other delimiters, if they appear.
    return [creator.strip() for creator in fm_record.director.split(",")]

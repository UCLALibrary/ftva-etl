import sys
import dateutil.parser
import string
import logging
from datetime import datetime
from typing import Optional

# Create a module logger, which will be a child of the package logger
logger = logging.getLogger(__name__)


def format_date(date_string: str, format: str = "%Y-%m-%d") -> str:
    """Format a date string to a given format.

    :param date_string: The date string to format.
    :param format: The format to use. Defaults to "%Y-%m-%d".
    :return: The formatted date string.
    :raises ValueError: If the date string cannot be parsed.
    """
    try:
        parsed_date = dateutil.parser.parse(date_string)
        return parsed_date.strftime(format)
    except dateutil.parser.ParserError:
        raise ValueError(f"'{date_string}' cannot be parsed to a date")


def _is_imprecise_date(date_string: str) -> bool:
    """Return True if date_string lacks full year-month-day precision.

    :param date_string: The date string to check.
    :return: True if the date string is imprecise, False otherwise.
    """
    # These are date format strings that indicate an imprecise date
    imprecise_date_formats = (
        "%Y-%m",  # Year-month, e.g. "1996-10"
        "%B, %Y",  # Month name, comma, and year, e.g. "October, 1996"
        "%b. %Y",  # Month abbreviation, period, and year, e.g. "Oct. 1996"
        "%B %Y",  # Month name, space, and year, e.g. "October 1996"
        "%b %Y",  # Month abbreviation, space, and year, e.g. "Oct 1996"
    )
    # Special check for 4-digit year with possible hyphen indicating an uncertain year.
    # Year only could be checked with `%Y` above, but it would not handle hyphens.
    # The check below returns True if:
    # 1. date_string is just a year (i.e. 4 digits); or
    # 2. date_string has a length of 4, and has hyphens to indicate an uncertain year,
    #    e.g. "202-" or "19--".
    if len(date_string) == 4 and (date_string.isdigit() or "-" in date_string):
        return True

    for format in imprecise_date_formats:
        try:
            # `strptime` will raise a ValueError
            # if the date string does not fully match the format.
            # Using it here as a pattern-matcher, not a parser.
            datetime.strptime(date_string, format)
            # If we get here, the date string matches one of the formats,
            # so it is imprecise and we return True.
            return True
        except ValueError:
            continue
    return False


def parse_date(date_string: str) -> str:
    """Parse a date string into a standardized format.

    :param date_string: Date string to parse.
    :return: Formatted date string, meaning:
    - a date formatted as YYYY-MM-DD if it can be parsed to a date;
    - the input string with trailing punctuation and whitespace removed
      if it cannot be parsed to a date, or if it is imprecise (i.e. not year-month-day precision).
    """

    # If the date string is in brackets, remove them temporarily
    # Remember this so we can add them back later
    in_brackets = "[" in date_string and "]" in date_string
    if in_brackets:
        date_string = date_string.replace("[", "").replace("]", "")

    # Remove trailing punctuation and whitespace
    date_string = date_string.rstrip(".,;:!?")
    date_string = date_string.strip()

    # If the date string is imprecise (i.e. not year-month-day precision), keep it as-is
    if _is_imprecise_date(date_string):
        formatted_date = date_string
    # Otherwise, try to parse the date string, handling any unexpected errors.
    else:
        try:
            parsed_date = dateutil.parser.parse(date_string)
            # Format the date as YYYY-MM-DD
            formatted_date = parsed_date.strftime("%Y-%m-%d")
        except (ValueError, dateutil.parser.ParserError) as e:
            # If parsing fails, log the error and return the original string.
            logger.warning(f"Failed to parse date '{date_string}': {e}")
            formatted_date = date_string

    if in_brackets:
        formatted_date = f"[{formatted_date}]"

    return formatted_date


def strip_whitespace_and_punctuation(items: list[str]) -> list[str]:
    """A utility function for striping whitespace and punctuation from lists of strings.

    :param items: A list of strings to strip.
    :return: The list of strings with whitespace and punctuation stripped.
    """
    # Add space to right-strip of punctuation to handle spaces after punctuation,
    # then explicitly strip square brackets and spaces from resulting string.
    return [item.rstrip(string.punctuation + " ").strip("[] ") for item in items]


def cleanup_production_type(production_type: str) -> list[str]:
    """Cleanup the production_type string to allow series identification.

    In the Filemaker PD, the production_type field is a list of strings,
    often delimited by carriage returns (\r).
    This function cleans up the string to allow series identification.

    :param production_type: A string containing the production types.
    :return: A list representation of the production types.
    """
    # Normalize to lowercase, split by carriage returns, then strip each item's whitespace
    return [item.strip() for item in production_type.lower().split("\r")]


def filter_by_inventory_number_and_library(
    records: list, inventory_number: str
) -> list:
    """Given a list of pymarc Records from Alma as obtained via SRU, and an inventory number
    (sourced from FTVA database), return a list of pymarc Records which match the inventory number
    and are from the FTVA library.

    :param records: A list of pymarc Records from Alma.
    :param inventory_number: The inventory number to match.
    :return: A list of pymarc Records from the FTVA library with matching
    inventory number.
    """

    filtered_records = []
    for record in records:
        # Holdings information is in the "availability" fields (tag AVA),
        # found within the MARC bib record provided by the SRU client.
        # There may be multiple AVA fields (one for each holding record), so get them all.
        fields_ava = record.get_fields("AVA")
        for field_ava in fields_ava:
            # $b is the library code, which should be "ftva" for FTVA records.
            # get_subfields() returns a list, but there should only be one $b and $d,
            # so just check the first one of each.
            library_code = field_ava.get_subfields("b")[0].lower()
            # $d is Call Number.
            call_number = field_ava.get_subfields("d")[0]

            if library_code == "ftva" and _is_inventory_number_match(
                inventory_number, call_number
            ):
                filtered_records.append(record)
                break  # No need to check other AVA fields for this record.

    return filtered_records


def _is_inventory_number_match(inventory_number: str, call_number: str) -> bool:
    """Given an inventory number (sourced from FTVA database) and a call number (sourced from
    Alma), return True if the Call Number matches the inventory number using guidelines provided
    by FTVA.

    :param inventory_number: The inventory number to check for.
    :param call_number: The call number of a bib record.
    :return: True if the inventory number matches the call number, False otherwise.
    """

    inv_no_prefixes = ["DVD", "HFA", "VA", "VD", "XFE", "XFF", "XVE", "ZVB"]
    call_no_suffixes = [" M", " R", " T"]

    # Exact match is always a match.
    if inventory_number == call_number:
        return True

    # If inventory number starts with a known prefix, check if it matches call number
    # with any added suffixes.
    for prefix in inv_no_prefixes:
        if inventory_number.startswith(prefix):
            for suffix in call_no_suffixes:
                if inventory_number + suffix == call_number:
                    return True

    return False


def _reset_handlers(logger: logging.Logger) -> None:
    """Reset the handlers of the provided logger.

    :param logger: The logger to reset the handlers of.
    """
    # Close then remove each handler
    for handler in logger.handlers:
        handler.close()
        logger.removeHandler(handler)


def configure_logging(
    enable_logging: bool = False,
    log_level: int = logging.INFO,
    handler: Optional[logging.Handler] = None,
    formatter: Optional[logging.Formatter] = None,
) -> None:
    """Configure logging for the package using the provided parameters, or defaults.

    :param enable_logging: Whether to enable logging. Defaults to False.
    :param log_level: The log level to use. Defaults to logging.INFO.
    :param handler: The handler to use. Will default to StreamHandler(sys.stdout)
        if not provided and enable_logging is True, otherwise will use NullHandler().
    :param formatter: The formatter to use. Will default to a standard format if not provided.
    """
    # Use the package name (i.e. `ftva_etl.metadata`) to get a logger
    # that will be a child of the logger created on package import.
    logger = logging.getLogger(__package__)

    # Reset the handlers to prevent multiple handlers being added
    _reset_handlers(logger)

    # If logging is disabled, set the logger level to CRITICAL and add a NullHandler,
    # which effectively disables logging.
    if not enable_logging:
        logger.setLevel(logging.CRITICAL)
        logger.addHandler(logging.NullHandler())
        return

    # Set the logger level, which defaults to INFO.
    logger.setLevel(log_level)
    # Default to logging to stdout.
    # stdout is specified explicitly, as default is stderr.
    if handler is None:
        handler = logging.StreamHandler(sys.stdout)
    # Default to a standard format.
    if formatter is None:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s: %(message)s"
        )
    handler.setFormatter(formatter)

    # We don't need to return the logger, as it can be accessed via the logger name
    logger.addHandler(handler)

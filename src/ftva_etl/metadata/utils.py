import dateutil.parser
import string


def parse_date(date_string: str) -> str:
    """Parse a date string into a standardized format.

    :param date_string: Date string to parse.
    :return: Formatted date string or an empty string if parsing fails."""

    # If the date string is in brackets, remove them temporarily
    # Remember this so we can add them back later
    in_brackets = "[" in date_string and "]" in date_string
    if in_brackets:
        date_string = date_string.replace("[", "").replace("]", "")

    # Remove trailing punctuation and whitespace
    date_string = date_string.rstrip(".,;:!?")
    date_string = date_string.strip()

    # Try to parse the date string using dateutil.parser
    # TODO: Add handling for underspecified dates, e.g. "2023" or "April 2023"
    try:
        parsed_date = dateutil.parser.parse(date_string)
        # Format the date as YYYY-MM-DD
        formatted_date = parsed_date.strftime("%Y-%m-%d")
    except (ValueError, dateutil.parser.ParserError):  # TODO: as e:
        # If parsing fails, log the error and return the original string
        # TODO: LOGGING
        # logging.info(f"Failed to parse date '{date_string}': {e}")
        formatted_date = date_string

    if in_brackets:
        formatted_date = f"[{formatted_date}]"

    return formatted_date


def strip_whitespace_and_punctuation(items: list[str]) -> list[str]:
    """A utility function for striping whitespace and punctuation from lists of strings.

    :param items: A list of strings to strip.
    :return: The list of strings with whitespace and punctuation stripped.
    """
    return [item.rstrip(string.punctuation).strip() for item in items]

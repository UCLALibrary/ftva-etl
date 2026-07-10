import logging

from fmrest.record import Record
from pathlib import PureWindowsPath, PurePosixPath
from .utils import cleanup_production_type


# Code which extracts data from a Filemaker record.

# Create a module logger, which will be a child of the package logger
logger = logging.getLogger(__name__)


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


def is_compilation(fm_record: Record) -> bool:
    """Determine if the `production_type` field represents a compilation,
    based on certain keywords defined in FTVA specs.

    :param fm_record: A Filemaker record.
    :return: True if the production type is a compilation, False otherwise.
    """

    production_type = cleanup_production_type(fm_record.production_type)
    title = fm_record.title.lower()
    if "compilation" in production_type or "compilation" in title:
        return True
    return False


def get_title_info(fm_record: Record, is_series: bool) -> dict:
    """Get the title info from a Filemaker record.

    :param fm_record: A Filemaker record.
    :param is_series: Whether the record is a series.
    :return: A dict containing the title info.
    """
    if is_compilation(fm_record):
        logger.info(
            f"Record with inventory id {fm_record.inventory_id} is identified as a compilation. "
            f"Production type: {fm_record.production_type}, title: {fm_record.title}"
        )
        return {}

    fm_title = fm_record.title.strip()
    # If no title found, log a warning and return an empty dict.
    if not fm_title:
        logger.warning(
            f"Record with inventory id {fm_record.inventory_id} has no title. "
        )
        return {}
    # If not a series, just return the title as-is.
    if not is_series:
        return {"title": fm_record.title}

    # For series, we want the series title, episode title, and episode number (if available).

    fm_ep_title = fm_record.episode_title.strip()
    # Space in field name means we have to use dict-style access to get the episode number field.
    fm_ep_no = fm_record["episode no."].strip()

    if fm_title and fm_ep_title and fm_ep_no:
        series_title = fm_title
        episode_title = fm_ep_title + ". " + fm_ep_no
        title = series_title + ". " + episode_title
        return {
            "title": title,
            "series_title": series_title,
            "episode_title": episode_title,
        }
    elif fm_title and fm_ep_title:
        series_title = fm_title
        episode_title = fm_ep_title
        title = series_title + ". " + episode_title
        return {
            "title": title,
            "series_title": series_title,
            "episode_title": episode_title,
        }
    elif fm_title and fm_ep_no:
        series_title = fm_title
        episode_title = fm_ep_no
        title = series_title + ". " + episode_title
        return {
            "title": title,
            "series_title": series_title,
            "episode_title": episode_title,
        }
    else:
        return {"title": fm_title}


def get_source_id(fm_record: Record) -> str:
    """Get the source identifier from a Filemaker record.

    :param fm_record: A Filemaker record.
    :return: The source identifier as a string.
    """
    return fm_record.source_identifier


def get_uuid(fm_record: Record) -> str:
    """Get the UUID from a Filemaker record.

    :param fm_record: A Filemaker record.
    :return: The UUID as a string.
    """
    return fm_record["UUID"]  # field name is capitalized in FM


def get_creation_date(fm_record: Record) -> str:
    """Get the creation date from a Filemaker record.

    :param fm_record: A Filemaker record.
    :return: The creation date as a string.
    """
    return fm_record["Creation_date"]  # note capitalization in field name


def get_asset_type(fm_record: Record) -> str:
    """Get the asset type from a Filemaker record.

    :param fm_record: A Filemaker record.
    :return: The asset type as a string.
    """
    return fm_record.asset_type


def get_media_type(fm_record: Record) -> str:
    """Get the media type from a Filemaker record.

    :param fm_record: A Filemaker record.
    :return: The media type as a string.
    """
    return fm_record.media_type


def get_audio_class(fm_record: Record) -> str:
    """Get the audio class from a Filemaker record.

    :param fm_record: A Filemaker record.
    :return: The audio class as a string.
    """
    # Specs say to return "Unknown" if this field is an empty string
    return fm_record.audio_class if fm_record.audio_class.strip() != "" else "Unknown"


def get_file_path_info(fm_record: Record) -> dict:
    """Get the file path info from a Filemaker record.

    :param fm_record: A Filemaker record.
    :return: A dict containing the file path info.
    """
    raw_value = fm_record.file_path
    try:
        # If raw value contains "\\", treat it as a Windows path,
        # otherwise treat it as a POSIX path
        file_path = (
            PureWindowsPath(raw_value)
            if "\\" in raw_value
            else PurePosixPath(raw_value)
        )

    except ValueError:
        logger.warning(
            f"Filemaker record with record ID {fm_record.recordId} "
            f"has an invalid `file_path` value: {raw_value}"
        )
        return {}

    if fm_record.specific_carrier_type.lower() == "dcp":
        return {
            "file_name": "",  # always empty for DCP
            "folder_name": file_path.parents[1].name,  # two levels up
            "sub_folder_name": file_path.parents[0].name,  # one level up
            "file_type": "DCP",
        }
    elif fm_record.specific_carrier_type.lower() == "dpx":
        return {
            "file_name": "",  # always empty for DPX
            "folder_name": file_path.parents[0].name,  # one level up
            "file_type": "DPX",
        }
    # If not a DCP or DPX, return just file name
    return {"file_name": file_path.name}

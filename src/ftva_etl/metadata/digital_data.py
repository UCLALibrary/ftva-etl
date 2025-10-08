# Code which extracts data from a Digital Data record.
# Minimal for now.
from uuid import UUID


def get_file_name(dd_record: dict) -> str:
    return dd_record.get("file_name", "")


def get_folder_name(dd_record: dict) -> str:
    return dd_record.get("file_folder_name", "")


def get_sub_folder_name(dd_record: dict) -> str:
    return dd_record.get("sub_folder_name", "")


def get_dd_record_id(dd_record: dict) -> int:
    return dd_record.get("id", 0)


def get_uuid(dd_record: dict) -> UUID | str:
    return dd_record.get("uuid", "")


def get_asset_type(dd_record: dict) -> str:
    return dd_record.get("asset_type", "")


def get_media_type(dd_record: dict) -> str:
    return dd_record.get("media_type", "")


def get_dcp_info(dd_record: dict) -> dict:
    """Return a bundle of fields for DCP files.

    :param dd_record: A Digital Data record
    :return: A dictionary of fields.
    """
    return {
        # File name must always be empty for DCPs.
        "file_name": "",
        "folder_name": get_folder_name(dd_record),
        "sub_folder_name": get_sub_folder_name(dd_record),
    }


def get_dpx_info(dd_record: dict) -> dict:
    """Return a bundle of fields for DPX files.

    :param dd_record: A Digital Data record
    :return: A dictionary of fields.
    """
    return {
        # File name must always be empty for DPXs.
        "file_name": "",
        "folder_name": get_folder_name(dd_record),
    }


def get_audio_class(dd_record: dict) -> str:
    """Return the audio class from a Digital Data record.

    :param dd_record: A Digital Data record
    :return: The audio class, or an empty string if not present.
    """
    return dd_record.get("audio_class", "")

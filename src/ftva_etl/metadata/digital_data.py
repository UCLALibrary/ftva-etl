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
    if dd_record.get("file_type") != "DCP":
        return {}
    return {
        # File name must always be empty for DCPs.
        "file_name": "",
        "folder_name": get_folder_name(dd_record),
        "sub_folder_name": get_sub_folder_name(dd_record),
        "file_type": "DCP",  # file type required by MAMS for DCP files
    }


def get_dpx_info(dd_record: dict) -> dict:
    """Return a bundle of fields for DPX files.

    :param dd_record: A Digital Data record
    :return: A dictionary of fields.
    """
    if dd_record.get("file_type") != "DPX":
        return {}
    return {
        # File name must always be empty for DPXs.
        "file_name": "",
        "folder_name": get_folder_name(dd_record),
        "file_type": "DPX",  # file type required by MAMS for DPX files
    }


def get_audio_class(dd_record: dict) -> str:
    """Return the audio class from a Digital Data record.

    :param dd_record: A Digital Data record
    :return: The audio class, or an empty string if not present.
    """
    return dd_record.get("audio_class", "")


def get_record_type_and_match_asset(dd_record: dict) -> dict:
    """Return the record type for a Digital Data record,
    and if applicable, the match asset for tracks.

    :param dd_record: A Digital Data record
    :return: A dictionary containing the record type,
    and if applicable, the match asset for tracks.
    """
    # Check if the DD record is a track,
    # indicated by an incoming relationship with a type of `isTrackOf`
    incoming_relationships = dd_record.get("incoming_relationships", [])
    # Get the first relationship with a type of `isTrackOf`,
    # or None if no such relationship is found.
    track_relationship = next(
        (
            relationship
            for relationship in incoming_relationships
            if relationship.get("relationship_type", "") == "isTrackOf"
        ),
        None,
    )
    # If a track relationship is found, set `record_type=track`
    # and `match_asset` to the source UUID for the relationship.
    if track_relationship:
        return {
            "record_type": "track",
            "match_asset": track_relationship.get("source_uuid"),
        }
    return {"record_type": "asset"}

# Code which extracts data from a Digital Data record.
# Minimal for now.
from uuid import UUID


def get_file_name(dd_record: dict) -> str:
    return dd_record.get("file_name", "")


def get_dd_record_id(dd_record: dict) -> int:
    return dd_record.get("id", 0)


def get_uuid(dd_record: dict) -> UUID | str:
    return dd_record.get("uuid", "")


def get_media_type(dd_record: dict) -> str:
    return dd_record.get("media_type", "")


def get_dcp_info(dd_record: dict) -> dict | None:
    dcp_info = {}
    file_type = dd_record.get("file_type", "")
    folder_name = dd_record.get("file_folder_name", "")
    if file_type == "DCP":
        if "DCP" in folder_name:
            dcp_info["asset_type"] = "Exhibition Copy"
            dcp_info["file_name"] = ""
            dcp_info["folder_name"] = dd_record.get("file_folder_name", "")
            dcp_info["sub_folder_name"] = dd_record.get("sub_folder_name", "")
            return dcp_info
    return None

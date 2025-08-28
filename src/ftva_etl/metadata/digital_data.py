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

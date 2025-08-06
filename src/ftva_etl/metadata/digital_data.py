# Code which extracts data from a Digital Data record.
# Minimal for now.


def get_file_name(dd_record: dict) -> str:
    return dd_record.get("file_name", "")


def get_dd_record_id(dd_record: dict) -> int:
    return dd_record.get("id", 0)

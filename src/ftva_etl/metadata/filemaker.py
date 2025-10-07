from fmrest.record import Record

# Code which extracts data from a Filemaker record.
# Minimal for now.


def get_inventory_id(fm_record: Record) -> str:
    return str(fm_record.inventory_id)


def get_inventory_number(fm_record: Record) -> str:
    return fm_record.inventory_no


def is_series_production_type(fm_record: Record) -> bool:
    production_type = fm_record.production_type
    serial_keywords = ["television series", "mini-series", "serials", "news"]
    return any(keyword in production_type.lower() for keyword in serial_keywords)

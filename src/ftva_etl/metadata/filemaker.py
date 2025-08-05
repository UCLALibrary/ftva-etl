from fmrest.record import Record


def get_inventory_id(fm_record: Record) -> str:
    return fm_record.inventory_id


def get_inventory_number(fm_record: Record) -> str:
    return fm_record.inventory_no

import spacy
from fmrest.record import Record as FM_Record
from pymarc import Record as Pymarc_Record
from .digital_data import get_dd_record_id, get_file_name
from .filemaker import get_inventory_id, get_inventory_number
from .marc import (
    get_bib_id,
    get_creators,
    get_date,
    get_language_name,
    get_title_info,
)


def get_mams_json(
    bib_record: Pymarc_Record, filemaker_record: FM_Record, digitaL_data_record: dict
) -> dict:
    # return json for the provided record only;
    # caller is responsible for managing multiple records.

    # Load spacy model for NER
    # TODO: Support use of a custom model, if needed
    nlp_model = spacy.load("en_core_web_md")

    titles = get_title_info(bib_record)
    asset = {
        "alma_mms_id": get_bib_id(bib_record),
        "inventory_id": get_inventory_id(filemaker_record),
        "dd_record_id": get_dd_record_id(digitaL_data_record),
        "inventory_number": get_inventory_number(filemaker_record),
        "release_broadcast_date": get_date(bib_record),
        "creator": get_creators(bib_record, nlp_model),
        "language": get_language_name(bib_record),
        **titles,
        "file_name": get_file_name(digitaL_data_record),
    }

    return asset

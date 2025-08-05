import spacy
from pymarc import Record
from .marc import (
    get_creators,
    get_date,
    get_language_name,
    get_record_id,
    get_title_info,
)


def get_mams_json(bib_record: Record, inventory_number: str) -> dict:
    # return json for the provided record only;
    # caller is responsible for managing multiple records.

    # Load spacy model for NER
    # TODO: Support use of a custom model, if needed
    nlp_model = spacy.load("en_core_web_md")

    titles = get_title_info(bib_record)
    asset = {
        "alma_mms_id": get_record_id(bib_record),
        "inventory_number": inventory_number,
        "release_broadcast_date": get_date(bib_record),
        "creator": get_creators(bib_record, nlp_model),
        "language": get_language_name(bib_record),
        **titles,
    }

    return asset

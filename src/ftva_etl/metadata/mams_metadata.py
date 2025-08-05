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


def get_mams_metadata(
    bib_record: Pymarc_Record, filemaker_record: FM_Record, digitaL_data_record: dict
) -> dict:
    """Generate JSON metadata for ingest into the FTVA MAMS.

    :param bib_record: A pymarc record, expected to contain bibliographic data.
    :param filemaker_record: A fmrest filemaker record.
    :param digital_data_record: A dict containing an FTVA digital data record.
    :return asset: A dict of metadata combined from the input records.
    """

    # Load spacy model for NER
    # TODO: Support use of a custom model, if needed?
    # Not sure yet where this should be loaded, or what performance impact
    # may be for batch processing.
    nlp_model = spacy.load("en_core_web_md")

    # This gets a collection of titles which will be unpacked later.
    titles = get_title_info(bib_record)

    # Get the rest of the data and prepare it for return.
    metadata = {
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

    return metadata

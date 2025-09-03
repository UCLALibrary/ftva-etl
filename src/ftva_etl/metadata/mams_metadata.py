import spacy
from fmrest.record import Record as FM_Record
from pymarc import Record as Pymarc_Record
from .digital_data import get_file_name, get_uuid, get_media_type, get_dcp_info
from .filemaker import get_inventory_id, get_inventory_number
from .marc import (
    get_bib_id,
    get_creators,
    get_date,
    get_language_name,
    get_title_info,
)


def get_mams_metadata(
    bib_record: Pymarc_Record,
    filemaker_record: FM_Record,
    digital_data_record: dict,
    match_asset_uuid: str | None = None,
) -> dict:
    """Generate JSON metadata for ingest into the FTVA MAMS.

    :param bib_record: A pymarc record, expected to contain bibliographic data.
    :param filemaker_record: A fmrest filemaker record.
    :param digital_data_record: A dict containing an FTVA digital data record.
    :param match_asset_uuid: A string representation of an asset's UUID. Defaults to None.
    :return asset: A dict of metadata combined from the input records.
    """

    # Load spacy model for NER
    # TODO: Support use of a custom model, if needed?
    # Not sure yet where this should be loaded, or what performance impact
    # may be for batch processing.
    nlp_model = spacy.load("en_core_web_md")

    # This gets a collection of titles which will be unpacked later.
    titles = get_title_info(bib_record)

    dcp_info = get_dcp_info(digital_data_record)

    # Get the rest of the data and prepare it for return.
    metadata = {
        "alma_bib_id": get_bib_id(bib_record),
        "inventory_id": get_inventory_id(filemaker_record),
        "uuid": get_uuid(digital_data_record),
        "inventory_number": get_inventory_number(filemaker_record),
        "creators": get_creators(bib_record, nlp_model),
        "release_broadcast_date": get_date(bib_record),
        "language": get_language_name(bib_record),
        "file_name": get_file_name(digital_data_record),
        "media_type": get_media_type(digital_data_record),
        **titles,
    }

    # If a match_asset_uuid is provided for a track, add it to the metadata record.
    if match_asset_uuid:
        metadata["match_asset"] = match_asset_uuid

    # If DCP info is present, update the metadata record with it.
    # Note that `file_name` will be overwritten for DCPs.
    if dcp_info:
        metadata.update(dcp_info)

    return metadata

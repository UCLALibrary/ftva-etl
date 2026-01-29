import spacy

from fmrest.record import Record as FM_Record
from pymarc import Record as Pymarc_Record
from typing import Optional

from .digital_data import (
    get_asset_type,
    get_dcp_info,
    get_dpx_info,
    get_file_name,
    get_media_type,
    get_uuid,
    get_audio_class,
)
from .filemaker import (
    get_inventory_id,
    get_inventory_number,
    is_series_production_type,
    get_creators as get_fm_creators,
    get_date_info as get_fm_date_info,
    get_language_name as get_fm_language_name,
)
from .marc import (
    get_bib_id,
    get_creators as get_alma_creators,
    get_date_info as get_alma_date_info,
    get_language_name as get_alma_language_name,
    get_title_info,
)


def get_mams_metadata(
    digital_data_record: dict,
    filemaker_record: FM_Record,
    bib_record: Optional[Pymarc_Record] = None,
    match_asset_uuid: Optional[str] = None,
) -> dict:
    """Generate JSON metadata for ingest into the FTVA MAMS.

    :param digital_data_record: A dict containing an FTVA digital data record.
    :param filemaker_record: A fmrest filemaker record.
        Optional to support multiple types of matching (e.g. DD-FM-Alma or DD-FM only).
    :param bib_record: A pymarc record, expected to contain bibliographic data.
        Optional to support multiple types of matching (e.g. DD-FM-Alma or DD-FM only).
    :param match_asset_uuid: A string representation of an asset's UUID. Defaults to None.
    :return asset: A dict of metadata combined from the input records.
    """

    # Load spacy model for NER
    # TODO: Support use of a custom model, if needed?
    # Not sure yet where this should be loaded, or what performance impact
    # may be for batch processing.
    nlp_model = spacy.load("en_core_web_md")

    alma_metadata = {}
    if bib_record:
        # Used for some special handling of serial titles
        is_series = is_series_production_type(filemaker_record)
        # This gets a collection of titles which will be unpacked later.
        titles = get_title_info(bib_record, is_series)
        alma_metadata = {
            "alma_bib_id": get_bib_id(bib_record),
            "language": get_alma_language_name(bib_record),
            "creators": get_alma_creators(bib_record, nlp_model),
            **titles,
            **get_alma_date_info(bib_record),
        }

    # Get the rest of the data and prepare it for return.
    metadata = {
        "alma": alma_metadata,
        "filemaker": {
            "inventory_id": get_inventory_id(filemaker_record),
            # All records returned from FM
            # should have only one inventory number for now,
            # but MAMS expects an array in JSON, so wrap in a list.
            # TODO: Parse comma-separated or otherwise delimited inventory numbers
            # from FM or other sources, if needed.
            "inventory_numbers": [get_inventory_number(filemaker_record)],
            "creators": get_fm_creators(filemaker_record),
            "language": get_fm_language_name(filemaker_record),
            **get_fm_date_info(filemaker_record),
        },
        "uuid": get_uuid(digital_data_record),
        "file_name": get_file_name(digital_data_record),
        "asset_type": get_asset_type(digital_data_record),
        "media_type": get_media_type(digital_data_record),
        "audio_class": get_audio_class(digital_data_record),
    }

    # If a match_asset_uuid is provided for a track, add it to the metadata record.
    if match_asset_uuid:
        metadata["match_asset"] = match_asset_uuid

    # Override some elements based on file type.
    file_type = digital_data_record.get("file_type", "")
    if file_type == "DCP":
        metadata.update(get_dcp_info(digital_data_record))
    elif file_type == "DPX":
        metadata.update(get_dpx_info(digital_data_record))
    else:
        # No special action needed
        pass

    return metadata

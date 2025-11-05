import spacy
from fmrest.record import Record as FM_Record
from pymarc import Record as Pymarc_Record
from .digital_data import (
    get_asset_type,
    get_dcp_info,
    get_dpx_info,
    get_file_name,
    get_media_type,
    get_uuid,
    get_audio_class,
)
from .filemaker import get_inventory_id, get_inventory_number, is_series_production_type
from .marc import (
    get_bib_id,
    get_creators,
    get_date_info,
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

    # Used for some special handling of serial titles
    is_series = is_series_production_type(filemaker_record)

    # This gets a collection of titles which will be unpacked later.
    titles = get_title_info(bib_record, is_series)

    # Get the date and qualifier.
    date_info = get_date_info(bib_record)

    # Get the rest of the data and prepare it for return.
    metadata = {
        "alma_bib_id": get_bib_id(bib_record),
        "inventory_id": get_inventory_id(filemaker_record),
        "uuid": get_uuid(digital_data_record),
        # All records returned from FM
        # should have only one inventory number for now,
        # but MAMS expects an array in JSON, so wrap in a list.
        # TODO: Parse comma-separated or otherwise delimited inventory numbers
        # from FM or other sources, if needed.
        "inventory_numbers": [get_inventory_number(filemaker_record)],
        "creators": get_creators(bib_record, nlp_model),
        "language": get_language_name(bib_record),
        "file_name": get_file_name(digital_data_record),
        "asset_type": get_asset_type(digital_data_record),
        "media_type": get_media_type(digital_data_record),
        "audio_class": get_audio_class(digital_data_record),
        **titles,
        **date_info,
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

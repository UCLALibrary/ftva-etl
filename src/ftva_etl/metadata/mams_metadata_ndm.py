import spacy

from fmrest.record import Record as FM_Record
from pymarc import Record as Pymarc_Record
from typing import Optional
from spacy.language import Language
from .filemaker import (
    get_inventory_id,
    get_inventory_number,
    get_source_id,
    is_series_production_type,
    get_creators as get_fm_creators,
    get_date_info as get_fm_date_info,
    get_language_name as get_fm_language_name,
    get_title_info as get_fm_title_info,
    get_uuid,
    get_creation_date,
    get_asset_type,
    get_media_type,
    get_audio_class,
    get_file_path_info,
)
from .marc import (
    get_bib_id,
    get_creators as get_alma_creators,
    get_date_info as get_alma_date_info,
    get_language_name as get_alma_language_name,
    get_title_info as get_alma_title_info,
)


def get_mams_metadata_ndm(
    fm_item_record: FM_Record,
    fm_inventory_record: FM_Record,
    alma_bib_record: Optional[Pymarc_Record] = None,
    match_asset: Optional[str] = None,
    nlp_model: Optional[Language] = None,
) -> dict:
    """Format metadata for output to the MAMS using new digital media (NDM) metadata sources.

    :param fm_item_record: A fmrest filemaker record containing item unit data.
    :param fm_inventory_record: A fmrest filemaker record containing inventory data.
    :param alma_bib_record: A pymarc record, expected to contain bibliographic data.
        Optional to support multiple types of matching (e.g. FM-Alma or FM only).
    :param match_asset: A string representation of the UUID for a related asset, if this is a track.
    :param nlp_model: A spacy language model to use for NER.
        If not provided, the default spacy model (en_core_web_md) will be used.
    :return: A dict containing the metadata formatted for output to the MAMS.
    """
    # Allow caller to provide the spacy model, to avoid loading it on every call
    if not nlp_model:
        nlp_model = spacy.load("en_core_web_md")

    # Used by both Filemaker and Alma metadata functions for determining how to format title info.
    # Filemaker is the source-of-truth for whether something is a series.
    is_series = is_series_production_type(fm_inventory_record)

    # These fields are derived from `fm_inventory_record`...
    fm_inventory_record_metadata = {
        "inventory_id": get_inventory_id(fm_inventory_record),
        # MAMS expects list for `inventory_numbers` field
        "inventory_numbers": [get_inventory_number(fm_inventory_record)],
        "source_id": get_source_id(fm_inventory_record),
        "creators": get_fm_creators(fm_inventory_record),
        "language": get_fm_language_name(fm_inventory_record),
        "asset_type": get_asset_type(fm_inventory_record),
        "media_type": get_media_type(fm_inventory_record),
        **get_fm_title_info(fm_inventory_record, is_series),
        **get_fm_date_info(fm_inventory_record),
    }

    # ...and these fields are derived from `fm_item_record`
    fm_item_record_metadata = {
        "uuid": get_uuid(fm_item_record),
        "creation_date": get_creation_date(fm_item_record),
        "audio_class": get_audio_class(fm_item_record),
        **get_file_path_info(fm_item_record),
    }

    alma_metadata = (
        {
            "alma_bib_id": get_bib_id(alma_bib_record),
            "language": get_alma_language_name(alma_bib_record),
            "creators": get_alma_creators(alma_bib_record, nlp_model),
            **get_alma_title_info(alma_bib_record, is_series),
            **get_alma_date_info(alma_bib_record),
        }
        if alma_bib_record
        else {}
    )

    # Unpack fields from Filemaker into a single metadata object...
    metadata = {
        "record_type": "asset",  # default to asset record type
        **fm_item_record_metadata,
        **fm_inventory_record_metadata,
    }

    # ...and if Alma metadata is available, update the metadata dict with Alma fields
    if alma_metadata:
        metadata.update(alma_metadata)

    # ...finally add match asset information, if provided
    if match_asset:
        # Update record type to track if match asset is provided
        metadata["record_type"] = "track"
        metadata["match_asset"] = match_asset

    # Sort the output dict by its keys, just to make review easier
    return dict(sorted(metadata.items()))

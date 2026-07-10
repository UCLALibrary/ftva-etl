import spacy
import logging

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


# Create a module logger, which will be a child of the package logger
logger = logging.getLogger(__name__)


def get_alma_metadata(
    bib_record: Pymarc_Record, nlp_model: Language, is_series: bool = False
) -> dict:
    """Get the Alma metadata from a pymarc record.

    :param bib_record: A pymarc record.
    :param nlp_model: A spacy language model to use for NER.
    :param is_series: Whether the record is a series, derived from Filemaker record.
        Defaults to False.
    :return: A dict containing the Alma metadata needed for the MAMS.
    """
    return {
        "alma_bib_id": get_bib_id(bib_record),
        "language": get_alma_language_name(bib_record),
        "creators": get_alma_creators(bib_record, nlp_model),
        **get_alma_title_info(bib_record, is_series),
        **get_alma_date_info(bib_record),
    }


def get_filemaker_metadata_from_inventory_record(
    fm_inventory_record: FM_Record, is_series: bool
) -> dict:
    """Get Filemaker metadata from the provided inventory record.

    :param fm_inventory_record: A Filemaker record containing inventory data.
    :param is_series: Whether the record is a series.
    :return: A dict containing the Filemaker metadata needed for the MAMS.
    """
    return {
        "inventory_id": get_inventory_id(fm_inventory_record),
        # All records returned from FM
        # should have only one inventory number for now,
        # but MAMS expects an array in JSON, so wrap in a list.
        # TODO: Parse comma-separated or otherwise delimited inventory numbers
        # from FM or other sources, if needed.
        "inventory_numbers": [get_inventory_number(fm_inventory_record)],
        "source_id": get_source_id(fm_inventory_record),
        "creators": get_fm_creators(fm_inventory_record),
        "language": get_fm_language_name(fm_inventory_record),
        "asset_type": get_asset_type(fm_inventory_record),
        "media_type": get_media_type(fm_inventory_record),
        **get_fm_title_info(fm_inventory_record, is_series),
        **get_fm_date_info(fm_inventory_record),
    }


def get_filemaker_metadata_from_item_record(fm_item_record: FM_Record) -> dict:
    """Get Filemaker metadata from the provided item record.

    :param fm_item_record: A Filemaker record containing item data.
    :param is_series: Whether the record is a series.
    :return: A dict containing the Filemaker metadata needed for the MAMS.
    """
    return {
        "uuid": get_uuid(fm_item_record),
        "creation_date": get_creation_date(fm_item_record),
        "audio_class": get_audio_class(fm_item_record),
        **get_file_path_info(fm_item_record),
    }


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

    fm_metadata_from_item_record = get_filemaker_metadata_from_item_record(
        fm_item_record
    )
    fm_metadata_from_inventory_record = get_filemaker_metadata_from_inventory_record(
        fm_inventory_record, is_series
    )

    alma_metadata = (
        get_alma_metadata(alma_bib_record, nlp_model, is_series)
        if alma_bib_record
        else {}
    )

    # Unpack fields from Filemaker into a single metadata object...
    metadata = {
        "record_type": "asset",  # default to asset record type
        **fm_metadata_from_item_record,
        **fm_metadata_from_inventory_record,
    }

    # ...and if Alma metadata is available, update the metadata dict with Alma fields
    if alma_metadata:
        metadata.update(alma_metadata)

    # ...finally add match asset information, if provided
    if match_asset:
        # Update record type to track if match asset is provided
        metadata["record_type"] = "track"
        metadata["match_asset"] = match_asset

    return metadata

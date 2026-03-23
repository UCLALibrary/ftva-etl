import spacy
import logging

from fmrest.record import Record as FM_Record
from pymarc import Record as Pymarc_Record
from typing import Optional
from spacy.language import Language
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
    get_title_info as get_fm_title_info,
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
    # This gets a collection of titles which will be unpacked later.
    titles = get_alma_title_info(bib_record, is_series)
    return {
        "alma_bib_id": get_bib_id(bib_record),
        "language": get_alma_language_name(bib_record),
        "creators": get_alma_creators(bib_record, nlp_model),
        **titles,
        **get_alma_date_info(bib_record),
    }


def get_filemaker_metadata(filemaker_record: FM_Record, is_series: bool) -> dict:
    """Get the Filemaker metadata from a Filemaker record.

    :param filemaker_record: A Filemaker record.
    :param is_series: Whether the record is a series, derived from Filemaker record.
    :return: A dict containing the Filemaker metadata needed for the MAMS.
    """
    titles = get_fm_title_info(filemaker_record, is_series)
    return {
        "inventory_id": get_inventory_id(filemaker_record),
        # All records returned from FM
        # should have only one inventory number for now,
        # but MAMS expects an array in JSON, so wrap in a list.
        # TODO: Parse comma-separated or otherwise delimited inventory numbers
        # from FM or other sources, if needed.
        "inventory_numbers": [get_inventory_number(filemaker_record)],
        "creators": get_fm_creators(filemaker_record),
        "language": get_fm_language_name(filemaker_record),
        **titles,
        **get_fm_date_info(filemaker_record),
    }


def _get_source_metadata(
    digital_data_record: dict,
    filemaker_record: FM_Record,
    bib_record: Optional[Pymarc_Record] = None,
    match_asset_uuid: Optional[str] = None,
) -> dict:
    """Retrieve and combine metadata from the source records into a single dict, for
    further processing and eventual output to the MAMS.

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

    # Determine if the record is a series, as determined by the Filemaker record.
    is_series = is_series_production_type(filemaker_record)

    filemaker_metadata = get_filemaker_metadata(filemaker_record, is_series)

    alma_metadata = (
        get_alma_metadata(bib_record, nlp_model, is_series) if bib_record else {}
    )

    # Get the rest of the data and prepare it for return.
    metadata = {
        "alma": alma_metadata,
        "filemaker": filemaker_metadata,
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


def get_mams_metadata(
    digital_data_record: dict,
    filemaker_record: FM_Record,
    bib_record: Optional[Pymarc_Record] = None,
    match_asset_uuid: Optional[str] = None,
) -> dict:
    """Format the source metadata for output to the MAMS.

    :param digital_data_record: A dict containing an FTVA digital data record.
    :param filemaker_record: A fmrest filemaker record.
        Optional to support multiple types of matching (e.g. DD-FM-Alma or DD-FM only).
    :param bib_record: A pymarc record, expected to contain bibliographic data.
        Optional to support multiple types of matching (e.g. DD-FM-Alma or DD-FM only).
    :param match_asset_uuid: A string representation of an asset's UUID. Defaults to None.
    :return: A dict containing the metadata formatted for output to the MAMS.
    """
    source_metadata = _get_source_metadata(
        digital_data_record, filemaker_record, bib_record, match_asset_uuid
    )
    # Begin structuring metadata for MAMS output.
    # For now, always assume we have a Filemaker record.
    metadata = {
        "inventory_id": source_metadata["filemaker"]["inventory_id"],
        "uuid": source_metadata["uuid"],
        "inventory_numbers": source_metadata["filemaker"]["inventory_numbers"],
        "file_name": source_metadata["file_name"],
        "asset_type": source_metadata["asset_type"],
        "media_type": source_metadata["media_type"],
        "audio_class": source_metadata["audio_class"],
    }
    # Folder and subfolder may be empty, depending on file type.
    # Match Asset may also be empty depending on asset/track relationships and matching results.
    # Only include if there is a value.
    if source_metadata.get("folder_name"):
        metadata["folder_name"] = source_metadata["folder_name"]
    if source_metadata.get("sub_folder_name"):
        metadata["sub_folder_name"] = source_metadata["sub_folder_name"]
    if source_metadata.get("match_asset"):
        metadata["match_asset"] = source_metadata["match_asset"]

    # 1-1-1 match: if we have Alma metadata, it is preferred over FM for certain fields.
    if source_metadata.get("alma"):
        metadata["alma_bib_id"] = source_metadata["alma"].get("alma_bib_id", "")
        metadata["creators"] = source_metadata["alma"].get("creators", [])
        metadata["language"] = source_metadata["alma"].get("language", "")
        # Get all fields with "title" in the name from alma metadata (e.g. title, series_title).
        alma_title_fields = {
            k: v for k, v in source_metadata["alma"].items() if "title" in k
        }
        metadata.update(alma_title_fields)
        # Get all date fields from alma metadata (e.g. release_broadcast_date, distribution_date).
        alma_date_info_fields = {
            k: v for k, v in source_metadata["alma"].items() if "date" in k
        }
        metadata.update(alma_date_info_fields)
    else:
        metadata["creators"] = source_metadata["filemaker"].get("creators", [])
        metadata["language"] = source_metadata["filemaker"].get("language", "")
        # Unpack FM title and date info if Alma metadata is not available.
        fm_title_fields = {
            k: v for k, v in source_metadata["filemaker"].items() if "title" in k
        }
        metadata.update(fm_title_fields)
        fm_date_info_fields = {
            k: v for k, v in source_metadata["filemaker"].items() if "date" in k
        }
        metadata.update(fm_date_info_fields)

    return metadata

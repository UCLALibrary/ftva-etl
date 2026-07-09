import spacy
import logging

from fmrest.record import Record as FM_Record
from pymarc import Record as Pymarc_Record
from typing import Optional
from spacy.language import Language
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


def _get_descriptive_metadata(source_metadata: dict) -> dict:
    """Utility for extracting descriptive metadata fields from the provided source,
    i.e. `creators`, `language`, and all title and date fields.
    Since these fields are common to both Alma and Filemaker sources,
    and Alma is preferred as a source when present, but is not required,
    this function is a reusable utility for extracting these fields from either source.

    :param source_metadata: A dict containing source metadata (i.e. either from Filemaker or Alma).
    :return: A dict containing descriptive metadata fields from the source metadata.
    """
    output = {
        "creators": source_metadata.get("creators", []),
        "language": source_metadata.get("language", ""),
        **{k: v for k, v in source_metadata.items() if "title" in k},
        **{k: v for k, v in source_metadata.items() if "date" in k},
    }
    return output


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

    filemaker_metadata = get_filemaker_metadata(fm_inventory_record, is_series)

    alma_metadata = (
        get_alma_metadata(alma_bib_record, nlp_model, is_series)
        if alma_bib_record
        else {}
    )

    # These are the fields from Filemaker
    filemaker_fields = {
        "inventory_id": filemaker_metadata.get("inventory_id", ""),
        "inventory_numbers": filemaker_metadata.get("inventory_numbers", []),
        **_get_descriptive_metadata(filemaker_metadata),
    }

    # Unpack fields from Filemaker into a single metadata object...
    metadata = {
        **filemaker_fields,
    }

    # ...and if Alma metadata is available, update the metadata dict with Alma fields
    if alma_metadata:
        alma_fields = {
            "alma_bib_id": alma_metadata.get("alma_bib_id", ""),
            **_get_descriptive_metadata(alma_metadata),
        }
        metadata.update(alma_fields)

    return metadata

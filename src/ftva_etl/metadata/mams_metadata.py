import spacy

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
    get_record_type_and_match_asset,
)
from .filemaker import (
    get_inventory_ids,
    get_inventory_numbers,
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


def get_mams_metadata(
    digital_data_record: dict,
    filemaker_record: FM_Record,
    bib_record: Optional[Pymarc_Record] = None,
    nlp_model: Optional[Language] = None,
) -> dict:
    """Format the source metadata for output to the MAMS.

    :param digital_data_record: A dict containing an FTVA digital data record.
    :param filemaker_record: A fmrest filemaker record.
    :param bib_record: A pymarc record, expected to contain bibliographic data.
        Optional to support multiple types of matching (e.g. DD-FM-Alma or DD-FM only).
    :param nlp_model: A spacy language model to use for NER.
        If not provided, the default spacy model (en_core_web_md) will be used.
    :return: A dict containing the metadata formatted for output to the MAMS.
    """
    # Allow caller to provide the spacy model, to avoid loading it on every call
    if not nlp_model:
        nlp_model = spacy.load("en_core_web_md")

    # Used by both Filemaker and Alma metadata functions for determining how to format title info.
    # Filemaker is the source-of-truth for whether something is a series.
    is_series = is_series_production_type(filemaker_record)

    # These are all the fields derived from the Digital Data app
    digital_data_fields = {
        "uuid": get_uuid(digital_data_record),
        "file_name": get_file_name(digital_data_record),
        "asset_type": get_asset_type(digital_data_record),
        "media_type": get_media_type(digital_data_record),
        "audio_class": get_audio_class(digital_data_record),
        **get_record_type_and_match_asset(digital_data_record),
        **get_dcp_info(digital_data_record),  # returns DCP fields if file type is DCP
        **get_dpx_info(digital_data_record),  # returns DPX fields if file type is DPX
    }

    # These are the fields from Filemaker
    filemaker_fields = {
        "inventory_id": get_inventory_ids(filemaker_record),
        # All records returned from FM
        # should have only one inventory number for now,
        # but MAMS expects an array in JSON, so wrap in a list.
        # TODO: Parse comma-separated or otherwise delimited inventory numbers
        # from FM or other sources, if needed.
        "inventory_numbers": get_inventory_numbers(filemaker_record),
        "creators": get_fm_creators(filemaker_record),
        "language": get_fm_language_name(filemaker_record),
        **get_fm_title_info(filemaker_record, is_series),
        **get_fm_date_info(filemaker_record),
    }

    alma_metadata = (
        {
            "alma_bib_id": get_bib_id(bib_record),
            "language": get_alma_language_name(bib_record),
            "creators": get_alma_creators(bib_record, nlp_model),
            **get_alma_title_info(bib_record, is_series),
            **get_alma_date_info(bib_record),
        }
        if bib_record
        else {}
    )

    # Combine fields from Digital Data and Filemaker into a single metadata object...
    metadata = {
        **digital_data_fields,
        **filemaker_fields,
    }

    # ...and if Alma metadata is available, update the metadata dict with Alma fields
    if alma_metadata:
        metadata.update(alma_metadata)

    # Sort the output dict by its keys, just to make review easier
    return dict(sorted(metadata.items()))

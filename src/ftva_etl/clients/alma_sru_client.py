import requests
import xml.etree.ElementTree as ET
from pymarc import parse_xml_to_array, Record, Field
from io import BytesIO


class AlmaSRUClient:
    def __init__(
        self, sru_url: str = "https://ucla.alma.exlibrisgroup.com/view/sru/01UCS_LAL"
    ) -> None:
        self._SRU_URL = sru_url
        # For our purposes, for now, hard-code these.
        self._SRU_DEFAULT_PARAMETERS = {
            "version": "1.2",
            "operation": "searchRetrieve",
            "recordSchema": "marcxml",
        }

    def search_by_call_number(self, call_number: str) -> list[Record]:
        """Fetches Alma data for a given call number.

        :param call_number: Call number to search in Alma.
        :return: List of pymarc records found by the search.
        """
        sru_response = self._search_alma(
            index="alma.PermanentCallNumber", search_term=call_number
        )
        return self._convert_sru_xml_to_marc_records(sru_response)

    def get_fields(self, marc_record: Record, tag_list: list[str]) -> list[Field]:
        """Extracts the specified fields from a MARC record.

        :param marc_record: A pymarc record.
        :param tag_list: A list of MARC tags, like ["001", "245"].
        :return: A list of pymarc fields matching the tag list.
        """
        # pymarc.Record.get_fields() needs to have list of tags unpacked:
        # get_fields("tag1", "tag2", ...)
        # get_fields returns an empty list if no fields found.
        # TODO: Return fields themselves, or friendlier representations?
        # print(f.tag, f.indicator1, f.indicator2, f.format_field())
        return marc_record.get_fields(self, *tag_list)

    def _search_alma(self, index: str, search_term: str) -> str:
        """Searches Alma via SRU, using the given index and search term.

        :param index: A valid Alma SRU index. TODO: Add 'explain' method to get indexes?
        :param search_term: A word or phrase to search for.
        :return: The XML from the response, as a UTF-8 encoded string.
        """
        # URL parameters are simple key/value strings, copy() is safe.
        params = self._SRU_DEFAULT_PARAMETERS.copy()

        # If the search term contains spaces, wrap it in double quotes.
        if " " in search_term:
            search_term = f'"{search_term}"'

        # Desired result is query=index=search_term;
        # as a request parameter, query: index=search_term
        query = {"query": f"{index}={search_term}"}
        params.update(query)

        # Do the search.
        response = requests.get(url=self._SRU_URL, params=params)

        # Alma SRU response status is still 200 even if invalid request sent;
        # consider checking for "diagnostic" (and more) XML in response.text,
        # but for now just raise exeeption if any non-OK response is received.
        response.raise_for_status()

        # No exception, so return response text.
        # TODO: what if no records found or other problems?
        return response.text

    def _convert_sru_xml_to_marc_records(self, sru_response: str) -> list[Record]:
        """Converts the XML returned by a SRU search into a list of pymarc records.

        :param sru_response: XML, as returned in an SRU search response.
        :return pymarc_records: A list of pymarc records.
        """

        # Convert the SRU response to an Element.
        root = ET.fromstring(sru_response)

        # Clear default namespace to avoid "ns0" prefix on records.
        ET.register_namespace("", "http://www.loc.gov/MARC21/slim")

        # Create short names for the XML namespaces in the response.
        namespaces = {
            "sru": "http://www.loc.gov/zing/srw/",
            "marc": "http://www.loc.gov/MARC21/slim",
        }

        # Find all MARCXML records embedded in the response.
        records = root.findall(
            "./sru:records/sru:record/sru:recordData/marc:record", namespaces
        )

        # Convert each MARCXML record to pymarc.Record.
        pymarc_records = []
        for record in records:
            # TODO: Possibly consolidate this with alma_marc.get_pymarc_record_from_bib;
            # core conversion is the same, but setup is different.
            marc_xml = ET.tostring(record, encoding="utf-8")
            # pymarc needs a file-like object to convert XML.
            with BytesIO(marc_xml) as fh:
                pymarc_record = parse_xml_to_array(fh)[0]
                pymarc_records.append(pymarc_record)

        return pymarc_records

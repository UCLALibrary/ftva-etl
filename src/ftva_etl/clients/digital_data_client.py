import requests


class DigitalDataClient:
    def __init__(
        self,
        user: str,
        password: str,
        url: str = "https://digital-data.cinema.ucla.edu",
    ) -> None:
        self._user = user
        self._password = password
        self._url = url

    def get_record_by_id(self, record_id: int) -> dict:
        """Get the FTVA Digital Data record matching the input record id.

        :param record_id: FTVA Digital Data record id.
        :return: All of the record's data.
        """
        url = f"{self._url}/records/{record_id}"
        return self._get_record(url)

    def get_records(
        self,
        offset: int | None = None,
        limit: int | None = None,
        query: str = "",
        fields: list[str] | None = None,
    ) -> dict:
        """Get FTVA Digital Data records with optional filtering and pagination.

        :param offset: Starting record for pagination. Defaults are applied by the API.
        :param limit: Number of results to return. Defaults are applied by the API.
        :param query: Optional search/filter string.
        :param fields: Optional list of fields to search in.
        :return: JSON from the response, containing records and total_records.
        """
        url = f"{self._url}/records/"
        params: dict[str, int | str] = {}
        # All params are optional, so set them only if they are provided.
        if offset:
            params["offset"] = offset
        if limit:
            params["limit"] = limit
        if query:
            params["query"] = query
        # Fields expected as a comma-separated string.
        if fields:
            params["fields"] = ",".join(fields)

        response = requests.get(url, auth=(self._user, self._password), params=params)
        response.raise_for_status()
        return response.json()

    def _get_record(self, url: str) -> dict:
        """General routine for fetching data.

        :param url: The fully formed URL for the request.
        :return: JSON from the response, containing all of the record's data.
        """
        # Very simple for now, matching the minimal REST API provided by
        # the FTVA Django application it calls.
        response = requests.get(url, auth=(self._user, self._password))
        response.raise_for_status()
        if response.status_code == 200:
            return response.json()
        else:
            return {}

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
        :return: Dict containing all of the record's data.
        :raises HTTPError: If response status code is 400-599.
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

        :param offset: Starting record for pagination. Default is 0, applied by the API.
        :param limit: Number of results to return. Default is 100, applied by the API.
        :param query: Optional search/filter string.
        :param fields: Optional list of fields to search in.
        :return: Dict containing `records` list and `total_records` count.
        :raises HTTPError: If response status code is 400-599.
        """
        url = f"{self._url}/records/"
        params: dict[str, int | str] = {}
        # All params are optional, so set them only if they are provided.
        if offset is not None:
            params["offset"] = offset
        if limit is not None:
            params["limit"] = limit
        if query:
            params["query"] = query
        # Fields expected as a comma-separated string.
        if fields:
            params["fields"] = ",".join(fields)

        response = requests.get(url, auth=(self._user, self._password), params=params)
        response.raise_for_status()
        if response.status_code == 200:
            return response.json()
        else:
            # NOTE: Fallback response format is hard-coded here,
            # in case the response status is unexpected,
            # i.e. not 200 and not 400-599.
            # Will need to update the format if the API changes.
            return {"records": [], "total_records": 0}

    def _get_record(self, url: str) -> dict:
        """General routine for fetching data.

        :param url: The fully formed URL for the request.
        :return: Dict containing all of the record's data.
        :raises HTTPError: If response status code is 400-599.
        """
        # Very simple for now, matching the minimal REST API provided by
        # the FTVA Django application it calls.
        response = requests.get(url, auth=(self._user, self._password))
        response.raise_for_status()
        if response.status_code == 200:
            return response.json()
        else:
            return {}

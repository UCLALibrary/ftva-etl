import fmrest
from fmrest.record import Record
from fmrest.exceptions import FileMakerError


class FilemakerClient:
    def __init__(
        self,
        user: str,
        password: str,
        url: str = "https://adam.cinema.ucla.edu",
        database: str = "Inventory for Labeling",
        layout: str = "InventoryForLabeling_ReadOnly_API",
        api_version: str = "vLatest",
        timeout: int = 120,
    ) -> None:

        # These are all required to initialize the Filemaker "Server" instance
        # (which is really a client, for talking to the server...).
        self._user = user
        self._password = password
        self._url = url
        self._database = database
        self._layout = layout
        self._api_version = api_version

        # timeout is not required, but the default can be too short for large queries.
        # 60 seconds seems enough for 5000 records; our default is double that.
        self._timeout = timeout

        # Initialize the Filemaker "Server" and store for later use.
        self._fms = fmrest.Server(
            url=self._url,
            user=self._user,
            password=self._password,
            database=self._database,
            layout=self._layout,
            api_version=self._api_version,
            timeout=self._timeout,
        )
        self._fms.login()

    @property
    def _default_fields(self) -> list[str]:
        return [
            "Acquisition type",
            "Alma",
            "aka",
            "availability",
            "director",
            "donor_code",
            "element_info",
            "episode no.",
            "episode_title",
            "film base",
            "format_type",
            "inventory_id",
            "inventory_no",
            "notes",
            "production_type",
            "release_broadcast_year",
            "spac",
            "title",
            "type",
        ]

    def search_by_inventory_number(self, inventory_number: str) -> list[Record]:

        records = self._search_filemaker(
            index="inventory_no", search_term=inventory_number
        )
        return records

    def get_fields(
        self, fm_record: Record, field_list: list[str] | None = None
    ) -> dict:
        """Gets the provided specific fields from a Filemaker Record instance.

        :param Record fm_record: A fmrest Record instance.
        :param list[str] specific_fields: A list of specific fields to get from the Record.
        (Default: `FM_PREVIEW_FIELDS`)
        :return: A dict with the specific fields from the Filemaker Record.
        Fields are only included if they exist in the Record.
        """
        if field_list is None:
            field_list = self._default_fields

        return {
            field: fm_record[field]
            for field in field_list
            if field in fm_record.to_dict()
        }

    def _search_filemaker(self, index: str, search_term: str) -> list[Record]:

        # Use Filemaker syntax for exact match (==) in query.
        # TODO: Extend this, if/when needed.
        query = [{index: f"=={search_term}"}]

        try:
            # `find()` raises an exception if no records are found for query,
            # rather than simply returning an empty `Foundset`-- hence the `try` block.
            # Also the date format in `find()` defaults to US format (MM-DD-YYYY);
            # set it to ISO-8601 (YYYY-MM-DD) instead.
            foundset = self._fms.find(query, date_format="iso-8601")
            # If no exception is raised, then foundset has 1 or more records.
            # Return it as a list to be consistent with empty list returned if no records found.
            return list(foundset)
        except FileMakerError as error:
            # FileMakerError doesn't provide the error code as an integer,
            # but rather as a string message, so check the string for
            # error 401, which represents "no records found".
            # Filemaker error codes @https://help.claris.com/en/pro-help/content/error-codes.html
            error_message = error.args[0]  # error message is first item in `args` tuple
            if "error 401" in error_message:
                return []  # if no records found, return an empty list
            # Re-raise the error if it's something other than 401--no records found
            raise error

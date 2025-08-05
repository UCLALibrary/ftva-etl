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
        # http://127.0.0.1:8000 for dev
        self._url = url

    def get_record_by_id(self, record_id: int) -> dict:
        url = f"{self._url}/records/{record_id}"
        return self._get_record(url)

    def _get_record(self, url: str) -> dict:
        response = requests.get(url, auth=(self._user, self._password))
        response.raise_for_status()
        if response.status_code == 200:
            return response.json()
        else:
            return {}

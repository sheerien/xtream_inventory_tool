# core/api.py

import requests
import time

class XtreamAPI:
    def __init__(self, host, username, password, timeout=30):
        self.host = host
        self.username = username
        self.password = password
        self.timeout = timeout

    def _call(self, params: dict, retries=2):
        params.update({
            "username": self.username,
            "password": self.password,
        })

        for _ in range(retries + 1):
            try:
                r = requests.get(
                    f"{self.host}/player_api.php",
                    params=params,
                    timeout=self.timeout
                )
                r.raise_for_status()
                return r.json() or {}
            except Exception:
                time.sleep(1)

        return {}

    def get_series_categories(self):
        return self._call({"action": "get_series_categories"}) or []

    def get_series(self, category_id):
        params = {"action": "get_series"}
        if category_id != "all":
            params["category_id"] = category_id
        return self._call(params) or []

    def get_series_info(self, series_id):
        return self._call({
            "action": "get_series_info",
            "series_id": series_id
        }) or {}

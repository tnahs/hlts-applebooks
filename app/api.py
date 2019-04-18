#!/usr/bin/env python3

import requests
import json
from typing import List, Union

from .defaults import ApiDefaults


class Api:

    def __init__(self, appconfig):

        self.appconfig = appconfig

        self.base_url = self.appconfig["base_url"]

        self.url_verify = f"{self.base_url}{ApiDefaults.url_verify}"
        self.url_refresh = f"{self.base_url}{ApiDefaults.url_refresh}"
        self.url_add = f"{self.base_url}{ApiDefaults.url_add}"

        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.appconfig['api_key']}"
        }

    def verify(self) -> Union[bool, Exception]:

        try:
            r = requests.get(self.url_verify, headers=self.headers)

            # API key verified.
            if r.status_code == 200:
                return True

            # Invalid API Key.
            elif r.status_code == 401:
                return False

            else:
                raise Exception(f"Unexpected Error: {r.status_code}")

        except requests.exceptions.ConnectionError:
            raise Exception("Connection Refused: The server is probably down...")

    def post(self, data: List[dict], method: str) -> Union[bool, Exception]:
        """ TODO: Cleanup up feedback method. This was written to be placed
        in a try/except block. Are we still going with that?
        """

        if method == "refresh":
            url = self.url_refresh
        elif method == "add":
            url = self.url_add
        else:
            raise Exception("Unrecognized API import method.")

        data = json.dumps(data)

        try:
            r = requests.post(url, data=data, headers=self.headers)

            try:
                response = r.json()
                for key, value in response.items():
                    if key != "response":
                        print(f"{key}: {value}")

            except json.decoder.JSONDecodeError:
                response = "No response from server..."

            if not r.status_code == 201:
                raise Exception(f"Unexpected Error: {r.status_code}\n{response}")

            else:
                return True

        except requests.exceptions.ConnectionError:
            raise Exception("Connection Refused: The server is probably down...")

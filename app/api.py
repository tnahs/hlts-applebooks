#!/usr/bin/env python3

import json
import requests

from .defaults import ApiDefaults


class ConnectToApi:

    def __init__(self, appconfig):

        url_base = appconfig["url_base"]
        api_key = appconfig["api_key"]

        self.url_verify = f"{url_base}{ApiDefaults.url_verify}"
        self.url_refresh = f"{url_base}{ApiDefaults.url_refresh}"
        self.url_add = f"{url_base}{ApiDefaults.url_add}"

        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        self._failures = []

    def verify(self):

        try:
            get = requests.get(self.url_verify, headers=self.headers)

            # API key verified.
            if get.status_code == 200:
                return True

            # Invalid API Key.
            elif get.status_code == 401:
                return False

            else:
                raise Exception(f"Unexpected Error: {get.status_code}")

        except requests.exceptions.ConnectionError:
            raise Exception("Connection Refused: The server is probably down...")

    def post(self, data, method):
        """ TODO: This is far too complex. Simplify. The way failues are sent
        back are a bit confusing. Need a clean way to check for any errors. """

        if method == "refresh":
            url = self.url_refresh

        elif method == "add":
            url = self.url_add

        else:
            raise Exception("Unrecognized API import method.")

        data = json.dumps(data)

        try:
            post = requests.post(url, data=data, headers=self.headers)

            try:
                response = post.json()

                api_response = response.get("api_response", None)

                if api_response not in ["SUCCESS", "FAILURES", "ERROR"]:
                    raise Exception(f"Unexpected Error: {post}")

                if api_response == "ERROR":
                    raise Exception(response["message"])

                elif api_response == "FAILURES":
                    self._failures.extend(response["failures"])

            except Exception as error:
                raise Exception(error)

        except requests.exceptions.ConnectionError:
            raise Exception("Connection Refused: The server is probably down...")

        except Exception as error:
            raise Exception(error)

    @property
    def failures(self):
        return self._failures

    @property
    def has_failures(self):
        """ Returns True if import experienced any failures. """
        return bool(self._failures)

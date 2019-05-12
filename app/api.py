#!/usr/bin/env python3

import sys
import json
import requests

from .defaults import ApiDefaults


class ApiConnect:

    def __init__(self, appconfig):

        self._response = []

        url_base = appconfig["url_base"]
        api_key = appconfig["api_key"]

        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        self.url_verify = f"{url_base}{ApiDefaults.url_verify}"
        self.url_refresh = f"{url_base}{ApiDefaults.url_refresh}"
        self.url_add = f"{url_base}{ApiDefaults.url_add}"

        self._url_error500 = f"{url_base}/api/error500"
        self._url_error400 = f"{url_base}/api/error400"
        self._url_error401 = f"{url_base}/api/error401"
        self._url_error403 = f"{url_base}/api/error403"
        self._url_error404 = f"{url_base}/api/error404"
        self._url_error405 = f"{url_base}/api/error405"

    def verify(self):
        """ TODO: After standardizing the API response re-write this method. """

        try:
            get = requests.get(self.url_verify, headers=self.headers)

            get.raise_for_status()

            # API key verified.
            if get.status_code == 200:
                return True

        except requests.exceptions.HTTPError as http_error:
            print(f"\nHTTP Error occurred: {http_error}")
            sys.exit(-1)

        except requests.exceptions.ConnectionError as connection_error:
            print(f"\nConnection Error occured: {connection_error}")
            sys.exit(-1)

        except Exception as unknown_error:
            print(f"\nUnknown Error occurred: {unknown_error}")
            sys.exit(-1)

    def post(self, data, method):
        """ TODO: After standardizing the API response re-write this method. """

        if method == "refresh":
            url = self.url_refresh

        elif method == "add":
            url = self.url_add

        else:
            raise Exception("Unrecognized API import method.")

        data = json.dumps(data)

        try:
            post = requests.post(url, data=data, headers=self.headers)

            post.raise_for_status()

            response = post.json()
            message = response.get("message", None)

            self._response.append(message)

        except requests.exceptions.HTTPError as http_error:
            print(f"\nHTTP Error occurred: {http_error}")
            sys.exit(-1)

        except requests.exceptions.ConnectionError as connection_error:
            print(f"\nConnection Error occured: {connection_error}")
            sys.exit(-1)

        except Exception as unknown_error:
            print(f"\nUnknown Error occurred: {unknown_error}")
            sys.exit(-1)

    @property
    def response(self):
        return json.dumps(self._response, sort_keys=True, indent=4)

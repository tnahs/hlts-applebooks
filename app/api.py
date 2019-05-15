#!/usr/bin/env python3

import json
import requests

from .defaults import ApiDefaults
from .errors import ApplicationError, ApiConnectionError


class ApiConnect:

    def __init__(self, app):

        self.app = app

        url_base = self.app.config.url_base
        api_key = self.app.config.api_key

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

        self._response = []

    def verify_key(self):
        """ TODO: After standardizing the API response re-write this method. """

        try:
            get = requests.get(self.url_verify, headers=self.headers)

            get.raise_for_status()

            # API key verified.
            if get.status_code == 200:
                return True

        except requests.exceptions.HTTPError as http_error:
            raise ApiConnectionError(repr(http_error), self.app)
        except requests.exceptions.ConnectionError as connection_error:
            raise ApiConnectionError(repr(connection_error), self.app)
        except Exception as unknown_error:
            raise ApiConnectionError(repr(unknown_error), self.app)

        return False

    def post(self, data, method):
        """ TODO: After standardizing the API response re-write this method. """

        if method == "refresh":
            url = self.url_refresh

        elif method == "add":
            url = self.url_add

        else:
            raise ApplicationError("Unrecognized API import method.", self.app)

        data = json.dumps(data)

        try:
            post = requests.post(url, data=data, headers=self.headers)

            post.raise_for_status()

            response = post.json()
            message = response.get("message", None)

            self._response.append(message)

        except requests.exceptions.HTTPError as http_error:
            ApiConnectionError(repr(http_error), self.app)
        except requests.exceptions.ConnectionError as connection_error:
            ApiConnectionError(repr(connection_error), self.app)
        except Exception as unknown_error:
            ApiConnectionError(repr(unknown_error), self.app)

    @property
    def response(self):
        return json.dumps(self._response, indent=4)

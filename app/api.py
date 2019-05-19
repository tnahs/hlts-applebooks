#!/usr/bin/env python3

import json
import requests

from .defaults import ApiDefaults
from .errors import ApplicationError, ApiConnectionError


class ApiConnect:

    def __init__(self, app):

        self.app = app

        self.url_base = self.app.config.url_base
        self.api_key = self.app.config.api_key

        self._import_succeeded = []
        self._import_failed = []

        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        """ TODO: Use a better method to joins these URLs. """
        self.url_verify = f"{self.url_base}{ApiDefaults.url_verify}"
        self.url_refresh = f"{self.url_base}{ApiDefaults.url_refresh}"
        self.url_add = f"{self.url_base}{ApiDefaults.url_add}"

        self.url_errors = [
            f"{self.url_base}/api/error500",
            f"{self.url_base}/api/error400",
            f"{self.url_base}/api/error401",
            f"{self.url_base}/api/error403",
            f"{self.url_base}/api/error404",
            f"{self.url_base}/api/error405",
        ]

    def verify_key(self):

        try:
            get = requests.get(self.url_verify, headers=self.headers)
            get.raise_for_status()
        except Exception as exception:
            ApiConnectionError(repr(exception), self.app)

        # API key verified.
        if get.status_code == 200:
            return True

        return False

    def import_annotations(self, data, method):

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
        except Exception as exception:
            ApiConnectionError(repr(exception), self.app)

        response = post.json()

        if post.status_code != 201:
            error = response.get("error")
            raise ApiConnectionError(error, self.app)

        data = response.get("data")
        import_failed = data.get("import_failed")
        import_succeeded = data.get("import_succeeded")

        self._import_failed.extend(import_failed)
        self._import_succeeded.append(import_succeeded)

    @property
    def had_failures(self):
        return bool(self._import_failed)

    @property
    def import_failed(self):
        """ Using json.dumps() to pretty print the dictionary.
        """
        return json.dumps(self._import_failed, indent=4)

    @property
    def import_succeeded(self):
        """ Using json.dumps() to pretty print the dictionary.
        """
        return json.dumps(self._import_succeeded, indent=4)

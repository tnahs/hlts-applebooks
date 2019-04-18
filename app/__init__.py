#!/usr/bin/env python3

import json

from .defaults import AppDefaults
from .applebooks import AppleBooks
from .api import Api
from .tools import OSTools


"""
TODO: Build custom exceptions.
"""


def generate_test_data(amount):

    test_data = []

    for num in range(amount):

        test_data.append(
            {
                "id": f"ID-{num}",
                "passage": f"Test passage #{num}!",
                "source": {
                    "name": "Testing Source",
                    "author": "Testing Author"
                },
                "notes": "",
                "tags": [],
                "collections": [],
                "metadata": {
                    "in_trash": False,
                    "is_protected": False,
                    "origin": "testing",
                    "modified": "",
                    "created": ""
                },
            }
        )

    return test_data


os = OSTools()


class App():

    def __init__(self):

        self._build_directories()
        self._load_config()
        # TODO: self._verify_config()

    def run(self):

        # self.applebooks = AppleBooks(self.config)
        self.api = Api(self.config)

        # self.add_annotations()
        # self.refresh_annotations()

    def add_annotations(self):

        data = generate_test_data(amount=100)

        # data = self.applebooks.adding_annotations
        chunks = self._chunk_data(data=data, chunk_size=50)

        if self.api.verify():
            print(f"Adding {len(data)} annotations...")
            for chunk in chunks:
                self.api.post(chunk, "add")

    def refresh_annotations(self):

        data = generate_test_data(amount=100)

        # data = self.applebooks.adding_annotations
        chunks = self._chunk_data(data=data, chunk_size=50)

        if self.api.verify():
            print(f"Refreshing {len(data)} annotations...")
            for chunk in chunks:
                self.api.post(chunk, "refresh")

    def _chunk_data(self, data: list, chunk_size):
        """ Instead of sending a long list of annotations all at once, this
        splits the list into a list of `chunk_size` lists. This helps prevent
        Request Timeouts.

        TODO: We need a non async api url to really test if this works. Right
        now it works really well with sending 5000 annotations. Not sure if it
        will work as well without the async url.
        """
        return [data[x:x + chunk_size] for x in range(0, len(data), chunk_size)]

    def _build_directories(self):

        # Create root_dir directory.
        os.make_dir(path=AppDefaults.root_dir)

        # Remove day_dir directory if it exists.
        os.delete_dir(path=AppDefaults.day_dir)

        # Creat new day_dir directory.
        for path in [AppDefaults.day_dir, AppDefaults.db_dir, AppDefaults.json_dir]:
            os.make_dir(path=path)

    def _load_config(self):

        try:
            with open(AppDefaults.config_file, "r") as f:
                self._config = json.load(f)
        except FileNotFoundError:
            self._set_default_config()
            self._save_config()
        except json.JSONDecodeError as error:
            raise Exception(error)
        except Exception as error:
            raise Exception(f"Unexpected Error: {repr(error)}")

    def _save_config(self):
        with open(AppDefaults.config_file, "w") as f:
            json.dump(self._config, f, sort_keys=True, indent=4, separators=(',', ': '))

    def _set_config(self, key, value):

        valid_keys = [
            "base_url",
            "api_key",
            "tag_prefix",
            "collection_prefix",
            "books_collections",
            "skip_color",
        ]

        if key not in valid_keys:
            raise KeyError("Invalid Config Key")

        self._config[key] = value

    def _set_default_config(self):

        self._config = {
            "base_url": "http://www.hlts.app",
            "api_key": "",
            "tag_prefix": "#",
            "collection_prefix": "@",
            "books_collections": {
                "add": "",
                "refresh": "",
                "ignore": ""
            },
            "skip_color": {
                "underline": False,
                "green": False,
                "blue": False,
                "yellow": False,
                "pink": False,
                "purple": False
            }
        }

    @property
    def config(self):
        return self._config

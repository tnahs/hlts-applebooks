#!/usr/bin/env python3

import json

from .defaults import AppDefaults
from .applebooks import AppleBooks
from .api import ConnectToApi
from .tools import OSTools, print_progress_bar
from .testing import generate_test_data


"""
TODO: Build custom exceptions. The ConnectToApi > Post Exception handling is
insane, we need better names so we understand exactly whats happening.

TODO: Cleanup the way we are recieving and bubbling up failures from the api.

TODO: Write a more explicit information response when an import happens.
Return a dictionary of data so we can display it.

TODO: Clean up all methods called in App.run()
"""


os = OSTools()


class App():

    def __init__(self):

        self._build_directories()
        self._load_config()

    def run(self):

        # self.applebooks = AppleBooks(self.config)
        self.api = ConnectToApi(self.config)

        self.add_annotations()
        self.refresh_annotations()

        if self.api.has_failures:
            print(f"Encountered {len(self.api.failures)} failures.")
            print(self.api.failures)

    def add_annotations(self):

        data = generate_test_data(amount=2000, offset=0)

        # data = self.applebooks.adding_annotations
        chunks = self._chunk_data(data=data, chunk_size=20)

        if self.api.verify():

            print(f"Adding {len(data)} annotations...")
            number_of_chunks = len(chunks)
            print_progress_bar(0, number_of_chunks)

            for i, chunk in enumerate(chunks):

                try:
                    self.api.post(chunk, "add")
                    print_progress_bar(i + 1, number_of_chunks)

                except Exception as error:
                    raise Exception(error)

    def refresh_annotations(self):

        data = generate_test_data(amount=2000, offset=0)

        # data = self.applebooks.adding_annotations
        chunks = self._chunk_data(data=data, chunk_size=20)

        if self.api.verify():

            print(f"Refreshing {len(data)} annotations...")
            number_of_chunks = len(chunks)
            print_progress_bar(0, number_of_chunks)
#
            for i, chunk in enumerate(chunks):

                try:
                    self.api.post(chunk, "refresh")
                    print_progress_bar(i + 1, number_of_chunks)

                except Exception as error:
                    raise Exception(error)

    def _chunk_data(self, data: list, chunk_size):
        """ Instead of sending a long list of annotations all at once, this
        splits the list into a list of `chunk_size` lists. This helps prevent
        Request Timeouts.
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
            "url_base",
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
            "url_base": "http://www.hlts.app",
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

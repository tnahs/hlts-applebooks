#!/usr/bin/env python3

import json

from .defaults import AppDefaults
from .applebooks import AppleBooks
from .api import Api
from .tools import OSTools


"""

TODO: The way the config is being passed is a bit much, kinda confusing.
Can we find a cleaner way to pass default variables?

TODO: Build custom exceptions.

"""


os = OSTools()


class App():

    def __init__(self):

        self._build_directories()
        self._load_config()
        # TODO: self._verify_config()

    def run(self):

        self.applebooks = AppleBooks(self.config)

        self.sync()

    def sync(self):

        api = Api(self.config)

        if api.verify():
            api.sync(data, "add")
            print("Syncing annotations...")

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

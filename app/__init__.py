#!/usr/bin/env python3

import sys
import json
from datetime import datetime

from .defaults import AppDefaults
from .applebooks import AppleBooks
from .api import ApiConnect
from .tools import OSTools, print_progress_bar
# from .testing import generate_dummy_annotations


"""
NOTE: The places we need to focus on are mainly the API and this app. We should
try and get clear communication and feedback between the two endpoints.

TODO: Build custom exceptions. The ApiConnect > Post Exception handling is
insane, we need better names so we understand exactly whats happening.

TODO: The way the config is being passed from AppleBooks to Annotation is kinda
confusing... Is there a cleaner way we can do that? It would be nice if we
could create a config object and pass that around the app without having to
pass it in the __init__ of a new object.

TODO: Add a way to append a temporary collection to the import. Anything that
is refreshed or added will get in a way "collection stamped" so you can see what
was added or refreshed today. "added-10121990" or "refreshed-10121990"

TODO: Implement your own standard API response. Like:

    {
        "success": true,
        "payload": {
            /* Application-specific data would go here. */
        }
    }

    {
        "success": false,
        "payload": {
            /* Application-specific data would go here. */
        },
        "error": {
            "code": 123,
            "message": "An error occurred!"
        }
    }

Or Like: https://github.com/omniti-labs/jsend

NOTE: Do we NEED an `add` *and* a `refresh` method? Could we just make it
only one method? What are the situations where it would be advantaeous to use
both. Doesn't the fact that we have a `protected` attribute allow us to just
stick with one method?

It seems that adding is way more efficent. Instead of deleting and re-adding
all un-changed annotations, it simply skips it.

TODO: Test out concatenated annotation syntax!
"""


os = OSTools()


class App:

    def __init__(self):

        self._build_directories()

        self.logger = Logger(self)
        self.config = Config(self)

    def run(self):

        self.applebooks = AppleBooks(self.config)
        self.api = ApiConnect(self.config)

        self.ask_confirmation()
        self.api.verify()
        self.send_annotations()
        self.display_api_response()

    def _build_directories(self):

        # Create root_dir directory.
        os.make_dir(path=AppDefaults.root_dir)

        # Remove day_dir directory if it exists.
        os.delete_dir(path=AppDefaults.day_dir)

        # Creat new day_dir directory.
        for path in [AppDefaults.day_dir, AppDefaults.db_dir, AppDefaults.json_dir]:
            os.make_dir(path=path)

    def ask_confirmation(self):

        """
        # Testing
        data_a = generate_dummy_annotations(count=50, id_prefix="TEST3")
        data_r = generate_dummy_annotations(count=25, id_prefix="TEST3")

        print(f"Found {len(data_a)} annotation to add.")
        print(f"Found {len(data_r)} annotation to refresh.")
        """

        num_add = self.applebooks.metadata["count"]["add"]
        num_refresh = self.applebooks.metadata["count"]["refresh"]

        print(f"Found {num_add} annotation to add.")
        print(f"Found {num_refresh} annotation to refresh.")

        if input("Confirm? [y/N] ").lower().strip() != "y":
            print("Exiting!")
            sys.exit(-1)

    def send_annotations(self):
        """ TODO: Clean and dry this code out. Maybe compact it so that we have
        only one progress bar? """

        """ Add annotations. """

        data = self.applebooks.adding_annotations
        # data = generate_dummy_annotations(count=1, id_prefix="TEST3")

        if data:

            chunked_data = self._chunk_data(data)
            number_of_chunks = len(chunked_data)

            print(f"Adding {len(data)} annotations...")
            print_progress_bar(0, number_of_chunks)

            for count, chunk in enumerate(chunked_data):

                self.api.post(chunk, "add")
                print_progress_bar(count + 1, number_of_chunks)

        """ Refresh annotations. """

        data = self.applebooks.refreshing_annotations
        # data = generate_dummy_annotations(count=10, id_prefix="TEST3")

        if data:

            chunked_data = self._chunk_data(data)
            number_of_chunks = len(chunked_data)

            print(f"Refreshing {len(data)} annotations...")
            print_progress_bar(0, number_of_chunks)

            for count, chunk in enumerate(chunked_data):

                self.api.post(chunk, "refresh")
                print_progress_bar(count + 1, number_of_chunks)

    def display_api_response(self):
        print(self.api.response)
        self.logger.info(self.api.response)

    def _chunk_data(self, data: list, chunk_size=100):
        """ Instead of sending a long list of annotations all at once, this
        splits the list into a list of `chunk_size` lists. This helps prevent
        Timeouts.
        """
        return [data[x:x + chunk_size] for x in range(0, len(data), chunk_size)]


class Logger:

    def __init__(self, app):

        self.app = app

        try:
            with open(AppDefaults.log_file, "r") as f:
                self._log = f.read()
        except FileNotFoundError:
            self._create_new_log()
        except Exception as error:
            raise Exception(f"Unexpected Error: {repr(error)}")

    def __repr__(self):
        return self._log

    def _create_new_log(self):
        with open(AppDefaults.log_file, "w") as f:
            f.write("")

    def _write_to_log(self, message):

        date = datetime.now().isoformat()

        try:
            with open(AppDefaults.log_file, "a") as f:
                f.write(f"{date} - {message}\n")
        except FileNotFoundError:
            self._create_new_log()
        except Exception as error:
            raise Exception(f"Unexpected Error: {repr(error)}")

    def info(self, info):
        self._write_to_log(f"INFO: {info}")

    def warning(self, warning):
        self._write_to_log(f"WARNING: {warning}")

    def error(self, error):
        self._write_to_log(f"ERROR: {error}")


class Config:

    def __init__(self, app):

        self.app = app

        try:
            with open(AppDefaults.config_file, "r") as f:
                _config = json.load(f)
                try:
                    # Base
                    self.env = _config["env"]
                    self.url_base = _config["url_base"]
                    self.api_key = _config["api_key"]
                    self.prefix_tag = _config["prefix_tag"]
                    self.prefix_collection = _config["prefix_collection"]
                    # Apple Books
                    self.applebooks_collections = _config["applebooks"]["collections"]
                    self.applebooks_colors = _config["applebooks"]["colors"]
                except KeyError as error:
                    self._config_load_error(error)
                    self._set_default_config()
                    self._save_config()
                except Exception as error:
                    raise Exception(f"Unexpected Error: {repr(error)}")
        except json.JSONDecodeError as error:
            self._config_load_error(error)
            self._set_default_config()
            self._save_config()
        except FileNotFoundError:
            self._set_default_config()
            self._save_config()
        except Exception as error:
            raise Exception(f"Unexpected Error: {repr(error)}")

    def __repr__(self):
        return str(self._serialize())

    def _config_load_error(self, error):
        """
        via. https://docs.python.org/3/library/pathlib.html#pathlib.Path.replace
        """
        self.app.logger.error(f"Error reading {AppDefaults.config_file}.")
        self.app.logger.error(repr(error))

        config_file = AppDefaults.config_file
        config_file_bak = config_file.with_suffix(".bak")

        config_file.replace(config_file_bak)

    def _set_default_config(self):

        self.app.logger.warning(f"Setting {AppDefaults.name} to default configuration.")

        self.env = ""
        self.url_base = "http://www.hlts.app"
        self.api_key = ""

        self.prefix_tag = "#"
        self.prefix_collection = "@"

        self.applebooks_collections = {
            "add": "",
            "refresh": "",
            "ignore": "",
        }
        self.applebooks_colors = {
            "underline": True,
            "green": True,
            "blue": True,
            "yellow": True,
            "pink": True,
            "purple": True,
        }

    def _save_config(self):

        self.app.logger.info(f"Saving {AppDefaults.config_file}...")

        with open(AppDefaults.config_file, "w") as f:
            json.dump(self._serialize(), f, indent=4, separators=(',', ': '))

    def _serialize(self):

        _config = {
            "env": self.env,
            "url_base": self.url_base,
            "api_key": self.api_key,
            "prefix_tag": self.prefix_tag,
            "prefix_collection": self.prefix_collection,
            "applebooks": {
                "collections": {
                    "add": self.applebooks_collections["add"],
                    "refresh": self.applebooks_collections["refresh"],
                    "ignore": self.applebooks_collections["ignore"],
                },
                "colors": {
                    "underline": self.applebooks_colors["underline"],
                    "green": self.applebooks_colors["green"],
                    "blue": self.applebooks_colors["blue"],
                    "yellow": self.applebooks_colors["yellow"],
                    "pink": self.applebooks_colors["pink"],
                    "purple": self.applebooks_colors["purple"]
                }
            }
        }

        return _config

#!/usr/bin/env python3

import json
from datetime import datetime

from .defaults import AppDefaults
from .applebooks import AppleBooks
from .api import ApiConnect
from .utilities import Utilities
from .errors import ApplicationError
from .testing import dummy_annotations


"""

NOTE: The places we need to focus on are mainly the hlts.api, hlts.data this
app. We should try and get clear communication and feedback between the two
endpoints.

TODO: Add a way to append a temporary collection to the import. Anything that
is refreshed or added will get in a way "collection stamped" so you can see what
was added or refreshed today. "added-10121990" or "refreshed-10121990"

TODO: Build custom exceptions.

TODO: Test out concatenated annotation syntax!

NOTE: `heroku run flask erase_all_annotations --app hlts-dev`
"""


class App:

    def __init__(self, debug=False):

        self.debug = debug
        self.utils = Utilities(self)

        self._build_directories()

        """ This proceeding order is important. We need to instantiate
        the Logger and Config objects before we can properly instantiate the
        ApiConnect and AppleBooks objects.

        All four take the the app as the first argument. This is how we are
        passing the app.config and app.logger to the rest of the application.
        """

        self.logger = Logger(self)
        self.config = Config(self)

        self.api = ApiConnect(self)
        self.applebooks = AppleBooks(self)

    def run(self):

        print(f"\nConnecting to {self.config.url_base}...")

        if self.api.verify_key():

            if self.debug:
                self._adding_annotations = dummy_annotations(
                    count=50, id_prefix="TEST1-adding", passage="Inital run.")
                self._refreshing_annotations = dummy_annotations(
                    count=50, id_prefix="TEST1-refreshing", passage="Inital run.")
            else:
                self.applebooks.manage()
                self._adding_annotations = self.applebooks.adding_annotations
                self._refreshing_annotations = self.applebooks.refreshing_annotations

            if self.user_confirm():
                self.handle_api_import()
                self.handle_api_response()

    def _build_directories(self):

        # Create app root_dir directory.
        self.utils.make_dir(path=AppDefaults.root_dir)

    def user_confirm(self):
        """ WIP: Placeholder function to handle user confirmation.
        """
        num_add = len(self._adding_annotations)
        num_refresh = len(self._refreshing_annotations)

        confirm = input(f"\nConfirm to add:{num_add} refresh:{num_refresh} annotations? [y/N]: ")

        if confirm.lower().strip() != "y":
            print("Confirmation cancelled.")
            return False

        return True

    def handle_api_import(self):
        """ TODO: Clean and DRY this code.
        QUESTION: Maybe compact it so that we have only one progress bar?
        """

        # Add annotations.
        if self._adding_annotations:

            chunked_data = self.utils.chunk_data(self._adding_annotations)
            number_of_chunks = len(chunked_data)

            print(f"Adding {len(self._adding_annotations)} annotations...")
            self.utils.print_progress(0, number_of_chunks)

            for count, chunk in enumerate(chunked_data):

                self.api.import_annotations(chunk, "add")
                self.utils.print_progress(count + 1, number_of_chunks)

        # Refresh annotations.
        if self._refreshing_annotations:

            chunked_data = self.utils.chunk_data(self._refreshing_annotations)
            number_of_chunks = len(chunked_data)

            print(f"Refreshing {len(self._refreshing_annotations)} annotations...")
            self.utils.print_progress(0, number_of_chunks)

            for count, chunk in enumerate(chunked_data):

                self.api.import_annotations(chunk, "refresh")
                self.utils.print_progress(count + 1, number_of_chunks)

    def handle_api_response(self):
        """ WIP: Placeholder function to handle API responses.
        """
        if self.api.had_failures:
            self.logger.warning(self.api.import_failed)
            print("WARNING: Encountered import failures. "
                  "Please check logs for details.")

        self.logger.info(self.api.import_succeeded)


class Logger:

    def __init__(self, app):

        self.app = app

        try:
            with open(AppDefaults.log_file, "r") as f:
                self._log = f.read()
        except FileNotFoundError:
            self._create_new_log()
        except Exception as error:
            raise ApplicationError(f"Unexpected Error: {repr(error)}", self.app)

    def __repr__(self):
        return self._log

    def _create_new_log(self):
        with open(AppDefaults.log_file, "w") as f:
            f.write("")

    def _write_to_log(self, message):

        date = datetime.now().strftime("%Y-%m-%d @ %I:%M:%S %p")

        message = f"{date} - {message}\n"

        try:
            with open(AppDefaults.log_file, "a") as f:
                f.write(message)
        except FileNotFoundError:
            self._create_new_log()
        except Exception as error:
            raise ApplicationError(f"Unexpected Error: {repr(error)}", self.app)

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
                    raise ApplicationError(f"Unexpected Error: {repr(error)}", self.app)
        except json.JSONDecodeError as error:
            self._config_load_error(error)
            self._set_default_config()
            self._save_config()
        except FileNotFoundError:
            self._set_default_config()
            self._save_config()
        except Exception as error:
            raise ApplicationError(f"Unexpected Error: {repr(error)}", self.app)

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
            json.dump(self._serialize(), f, indent=4)

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

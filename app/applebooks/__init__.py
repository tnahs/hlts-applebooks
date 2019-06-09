#!/usr/bin/env python3

import re
import json
import psutil
import pathlib
import sqlite3
from pathlib import Path
from datetime import datetime

from .defaults import AppleBooksDefaults
from .errors import AppleBooksError


home = Path.home()
date = datetime.now().strftime("%Y%m%d")


class AppleBooks:

    def __init__(self, app):

        self.app = app

        self._build_directories()

    def manage(self):

        if self._applebooks_running():
            raise AppleBooksError("Apple Books currently running.", self.app)

        self._copy_databases()
        self._query_applebooks_db()
        self._build_annotations()
        self._sort_annotations()

    def _applebooks_running(self):
        """ Check to see if AppleBooks is currently running.
        """

        for proc in psutil.process_iter():

            try:
                pinfo = proc.as_dict(attrs=["name"])
            except psutil.NoSuchProcess:
                """ When a process doesn't have a name it might mean it's a
                zombie process which ends up raising a NoSuchProcess exception
                or its subclass the ZombieProcess exception.
                """
                pass
            except Exception as error:
                raise AppleBooksError(f"Unexpected Error: {repr(error)}", self.app)

            if pinfo["name"] == "Books":
                return True

        return False

    def _build_directories(self):
        """ Build all relevant directories for AppleBooks. We dont create the
        directories for local_bklibrary_dir and local_aeannotation_dir seeing
        as these are created when the source databases are copied over. """

        # Create local_root_dir
        self.app.utils.make_dir(path=AppleBooksDefaults.local_root_dir)

        # Delete local_day_dir. Just in case app is run more than once a day.
        self.app.utils.delete_dir(path=AppleBooksDefaults.local_day_dir)

        # Creat new local_day_dir and local_db_dir directory.
        for path in [AppleBooksDefaults.local_day_dir, AppleBooksDefaults.local_db_dir]:
            self.app.utils.make_dir(path=path)

    def _copy_databases(self):
        """ Copy AppleBooks database directories to Local Data directories. """

        # Copy directory containing BKLibrary###.sqlite files.
        self.app.utils.copy_dir(
            src=AppleBooksDefaults.src_bklibrary_dir,
            dest=AppleBooksDefaults.local_bklibrary_dir)

        # Copy directory containing AEAnnotation###.sqlite files.
        self.app.utils.copy_dir(
            src=AppleBooksDefaults.src_aeannotation_dir,
            dest=AppleBooksDefaults.local_aeannotation_dir)

    def _query_applebooks_db(self):

        self.db = ConnectToAppleBooksDB(self.app)

        self._raw_sources = self.db.query_sources()
        self._raw_annotations = self.db.query_annotations()

    def _build_annotations(self):
        """ TODO: Document what this code is doing and how it's doing it."""

        self._annotations = []

        for raw_annotation in self._raw_annotations:

            for raw_source in self._raw_sources:

                if raw_annotation["source_id"] == raw_source["id"]:

                    """ TODO: Not sure what this if block is checking. """
                    if not raw_annotation.get("source") \
                       and not raw_annotation.get("author"):
                        raw_annotation["source"] = raw_source["name"]
                        raw_annotation["author"] = raw_source["author"]

                    try:
                        raw_annotation["applebooks_collections"]
                    except KeyError:
                        raw_annotation["applebooks_collections"] = []
                    finally:
                        raw_annotation["applebooks_collections"].append(raw_source["books_collection"])

            annotation = Annotation(self.app, raw_annotation)

            self._annotations.append(annotation)

    def _sort_annotations(self):
        """ If an annotation contains two conflicting "applebooks_collections", it
        will sorted in this order: skip > ignore > refresh > add > unsorted.
        The strongest in the list is "skip" followed by "ignore" all the way
        down the line to "add". Everything else that remains is placed into
        "unsorted" which acts as a catch-all if no collections are specified.

        TODO: Clean variable names here. It's kinda messy and confusing. Also,
        will anything ever make it into the "unsorted" bin with our current
        setup?
        """

        self._adding = []
        self._refreshing = []
        self._ignoring = []
        self._skipping = []
        self._unsorted = []

        abc_config = self.app.utils.to_lowercase(self.app.config.applebooks_collections)

        adding_collection = abc_config.get("add", "")
        refreshing_collection = abc_config.get("refresh", "")
        ignoring_collection = abc_config.get("ignore", "")

        for annotation in self._annotations:

            applebooks_collections = self.app.utils.to_lowercase(annotation._applebooks_collections)

            if annotation.is_skipped:
                self._skipping.append(annotation)
                continue

            if ignoring_collection in applebooks_collections:
                self._ignoring.append(annotation)

            elif refreshing_collection in applebooks_collections:
                self._refreshing.append(annotation)

            elif adding_collection in applebooks_collections:
                self._adding.append(annotation)

            else:
                self._unsorted.append(annotation)

    @property
    def data(self):

        data = {
            "all": self.all_annotations,
            "add": self.adding_annotations,
            "refresh": self.refreshing_annotations,
            "ignore": self.ignoring_annotations,
            "skip": self.skipping_annotations,
            "unsorted": self.unsorted_annotations,
            "metadata": self.metadata
        }

        return data

    @property
    def metadata(self):

        data = {
            "date": datetime.utcnow().isoformat(),
            "count": {
                "all": len(self.all_annotations),
                "add": len(self.adding_annotations),
                "refresh": len(self.refreshing_annotations),
                "ignore": len(self.ignoring_annotations),
                "skip": len(self.skipping_annotations),
                "unsorted": len(self.unsorted_annotations),
            }
        }

        return data

    @staticmethod
    def _to_multiple_dict(annotations):
        return [annotation.serialize() for annotation in annotations]

    @property
    def all_annotations(self):
        return self._to_multiple_dict(self._annotations)

    @property
    def adding_annotations(self):
        return self._to_multiple_dict(self._adding)

    @property
    def refreshing_annotations(self):
        return self._to_multiple_dict(self._refreshing)

    @property
    def ignoring_annotations(self):
        return self._to_multiple_dict(self._ignoring)

    @property
    def skipping_annotations(self):
        return self._to_multiple_dict(self._skipping)

    @property
    def unsorted_annotations(self):
        return self._to_multiple_dict(self._unsorted)

    def export_to_json(self, directory, filename):
        with open(directory / filename, 'w') as f:
            json.dump(self.data, f, indent=4)


class Annotation:

    def __init__(self, app, data: dict):

        self.app = app
        self.data = data

        self._process_passage()
        self._process_notes()

    def _process_passage(self):

        passage = self.data["passage"]

        self._passage = passage.replace("\n", "\n\n")

    def _process_notes(self):
        """ TODO: This whole method is really hard to understand. Can we
        possibly simplify it in any way?
        """

        _notes = self.data["notes"]

        prefix_tag = self.app.config.prefix_tag
        prefix_collection = self.app.config.prefix_collection

        re_prefix_tag = re.compile(prefix_tag)
        re_tag_pattern = re.compile(self._re_pattern(prefix_tag))
        re_prefix_collection = re.compile(prefix_collection)
        re_collection_pattern = re.compile(self._re_pattern(prefix_collection))

        if _notes:

            # Extract tags from notes.
            tags = re.findall(re_tag_pattern, _notes)
            tags = [tag.strip() for tag in tags]
            tags = [re.sub(re_prefix_tag, "", tag) for tag in tags]

            # Extract collections from notes.
            collections = re.findall(re_collection_pattern, _notes)
            collections = [collection.strip() for collection in collections]
            collections = [re.sub(re_prefix_collection, "", collection) for collection in collections]

            # Remove tags from notes.
            notes = re.sub(re_tag_pattern, "", _notes)
            notes = re.sub(re_collection_pattern, "", notes)
            notes = notes.strip()

        else:

            notes = ""
            tags = []
            collections = []

        self._notes = notes
        self._tags = tags
        self._collections = collections

    def _re_pattern(self, prefix):
        return f"\B{prefix}[^{prefix}\s]+\s?"

    def _convert_date(self, epoch: float) -> str:
        """ Converts Epoch to ISO861"""

        seconds_since_epoch = float(epoch) + AppleBooksDefaults.ns_time_interval_since_1970

        date = datetime.utcfromtimestamp(seconds_since_epoch)
        date = date.isoformat()

        return date

    @property
    def id(self):
        return self.data["id"]

    @property
    def passage(self):
        return self._passage

    @property
    def notes(self):
        return self._notes

    @property
    def source_name(self):
        return self.data["source"]

    @property
    def source_author(self):
        return self.data["author"]

    @property
    def tags(self):
        return self._tags

    @property
    def collections(self):
        return self._collections

    @property
    def created(self):
        return self._convert_date(self.data["created"])

    @property
    def modified(self):
        return self._convert_date(self.data["modified"])

    @property
    def _color(self):
        return self.data["color"]

    @property
    def _applebooks_collections(self):
        return self.data["applebooks_collections"]

    @property
    def is_skipped(self):
        """ Skip annotations based on User Config. """

        color = self._color

        if color == 0 and self.app.config.applebooks_colors["underline"]:
            return False
        if color == 1 and self.app.config.applebooks_colors["green"]:
            return False
        if color == 2 and self.app.config.applebooks_colors["blue"]:
            return False
        if color == 3 and self.app.config.applebooks_colors["yellow"]:
            return False
        if color == 4 and self.app.config.applebooks_colors["pink"]:
            return False
        if color == 5 and self.app.config.applebooks_colors["purple"]:
            return False

        return True

    def serialize(self):

        data = {
            "id": self.id,
            "passage": self.passage,
            "notes": self.notes,
            "source": {
                "name": self.source_name,
                "author": self.source_author,
            },
            "tags": self.tags,
            "collections": self.collections,
            "metadata": {
                "created": self.created,
                "modified": self.modified,
                "origin": AppleBooksDefaults.origin,
                "is_protected": False,
                "in_trash": False,
            }
        }

        return data


class ConnectToAppleBooksDB:

    def __init__(self, app):

        self.app = app

        self.bklibrary_sqlite = self._get_sqlite(path=AppleBooksDefaults.local_bklibrary_dir)
        self.aeannotation_sqlite = self._get_sqlite(path=AppleBooksDefaults.local_aeannotation_dir)

    def query_sources(self):

        data = self._execute_query(
            sqlite_file=self.bklibrary_sqlite,
            query=AppleBooksDefaults.source_query)

        return data

    def query_annotations(self):

        data = self._execute_query(
            sqlite_file=self.aeannotation_sqlite,
            query=AppleBooksDefaults.annotation_query)

        return data

    def _get_sqlite(self, path: pathlib.Path) -> pathlib.Path:
        """ Glob full database path.
        """
        sqlite_file = list(path.glob("*.sqlite"))

        try:
            sqlite_file = sqlite_file[0]
            return sqlite_file
        except IndexError:
            raise AppleBooksError(f"Couldn't find AppleBooks database @ {path}.", self.app)

    def _execute_query(self, sqlite_file, query) -> list:

        connection = self._connect_to_db(sqlite_file=sqlite_file)

        with connection:
            cursor = connection.cursor()
            cursor.execute(query)
            data = cursor.fetchall()

        return data

    def _connect_to_db(self, sqlite_file: pathlib.Path) -> sqlite3.Connection:
        """ Create a database connection to SQLite database
        """
        try:
            connection = sqlite3.connect(sqlite_file)
            connection.row_factory = self._dict_factory
            return connection
        except sqlite3.Error as error:
            raise AppleBooksError(f"SQLite Error: {repr(error)}", self.app)

        return None

    def _dict_factory(self, cursor: sqlite3.Cursor, row: tuple) -> dict:

        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]

        return d

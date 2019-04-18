#!/usr/bin/env python3

import re
import json
import sqlite3
import pathlib
from pathlib import Path
from datetime import datetime

from .defaults import AppDefaults, AppleBooksDefaults
from .tools import OSTools, to_lower


home = Path.home()
date = datetime.now().strftime("%Y%m%d")


os = OSTools()


class AppleBooks():

    def __init__(self, appconfig):

        self.appconfig = appconfig

        self.date = datetime.utcnow().isoformat()

        self._copy_databases()
        self._compile_annotations()
        self._sort_annotations()

    def _copy_databases(self):

        # Copy BKLibrary###.sqlite files
        os.copy_dir(src=AppleBooksDefaults.bklibrary_dir,
                    dest=AppDefaults.bklibrary_dir)

        # Copy AEAnnotation###.sqlite files
        os.copy_dir(src=AppleBooksDefaults.aeannotation_dir,
                    dest=AppDefaults.aeannotation_dir)

    def _compile_annotations(self):
        """ Merge annotation with source based on "source_id".
        """

        self._annotations = []

        query = QueryAppleBooks()

        self._raw_sources = query.all_sources()
        self._raw_annotations = query.all_annotations()

        for raw_annotation in self._raw_annotations:

            for raw_source in self._raw_sources:

                if raw_annotation["source_id"] == raw_source["id"]:

                    if not raw_annotation.get("source") and not raw_annotation.get("author"):
                        raw_annotation["source"] = raw_source["name"]
                        raw_annotation["author"] = raw_source["author"]

                    try:
                        raw_annotation["books_collections"]
                    except KeyError:
                        raw_annotation["books_collections"] = []
                    finally:
                        raw_annotation["books_collections"].append(raw_source["books_collection"])

            annotation = Annotation(self.appconfig, raw_annotation)

            self._annotations.append(annotation)

    def _sort_annotations(self):
        """ If an annotation contains two conflicting "books_collections", it
        will sorted in this order: skip > ignore > refresh > add. "Skip" is the
        strongest in the list followed by "ignore" all the way down the line to
        "add" which can act as a catch-all if no "add" collection is specified.
        """

        self._adding = []
        self._refreshing = []
        self._ignoring = []
        self._skipping = []

        books_collections = to_lower(self.appconfig["books_collections"])

        adding_collection = books_collections.get("add", "")
        refreshing_collection = books_collections.get("refresh", "")
        ignoring_collection = books_collections.get("ignore", "")

        for annotation in self._annotations:

            if annotation.is_skipped:
                self._skipping.append(annotation)
                continue

            books_collections = to_lower(annotation.books_collections)

            if ignoring_collection in books_collections:
                self._ignoring.append(annotation)

            elif refreshing_collection in books_collections:
                self._refreshing.append(annotation)

            elif adding_collection in books_collections or adding_collection == "":
                self._adding.append(annotation)

    @staticmethod
    def serialize(item):
        return [x.to_dict() for x in item]

    @property
    def all_annotations(self):
        return self.serialize(self._annotations)

    @property
    def sorted_annotations(self):

        data = {
            "all": self.all_annotations,
            "add": self.adding_annotations,
            "refresh": self.refreshing_annotations,
            "ignore": self.ignoring_annotations,
            "skip": self.skipping_annotations,
            "metadata": self.info
        }

        return data

    @property
    def info(self):

        data = {
            "date": self.date,
            "count": {
                "all": len(self.all_annotations),
                "add": len(self.adding_annotations),
                "refresh": len(self.refreshing_annotations),
                "ignore": len(self.ignoring_annotations),
                "skip": len(self.skipping_annotations),
            }
        }

        return data

    @property
    def adding_annotations(self):
        return self.serialize(self._adding)

    @property
    def refreshing_annotations(self):
        return self.serialize(self._refreshing)

    @property
    def ignoring_annotations(self):
        return self.serialize(self._ignoring)

    @property
    def skipping_annotations(self):
        return self.serialize(self._skipping)

    def export_to_json(self, directory, filename):

        with open(directory / filename, 'w') as f:
            json.dump(self.sorted_annotations, f, sort_keys=True, indent=4, separators=(',', ': '))


class Annotation:

    def __init__(self, appconfig, data: dict):

        self.appconfig = appconfig
        self.data = data

        self._process_passage()
        self._process_notes()

    def _process_passage(self):

        passage = self.data["passage"]

        self._passage = passage.replace("\n", "\n\n")

    def _re_pattern(self, prefix):
        return f"\B{prefix}[^{prefix}\s]+\s?"

    def _process_notes(self):

        notes = self.data["notes"]

        re_tag_prefix = re.compile(self.appconfig["tag_prefix"])
        re_tag_pattern = re.compile(self._re_pattern(self.appconfig["tag_prefix"]))
        re_collection_prefix = re.compile(self.appconfig["collection_prefix"])
        re_collection_pattern = re.compile(self._re_pattern(self.appconfig["collection_prefix"]))

        if notes:

            # Extract tags from notes.
            tags = re.findall(re_tag_pattern, notes)
            tags = [tag.strip() for tag in tags]
            tags = [re.sub(re_tag_prefix, "", tag) for tag in tags]

            # Extract collections from notes.
            collections = re.findall(re_collection_pattern, notes)
            collections = [collection.strip() for collection in collections]
            collections = [re.sub(re_collection_prefix, "", collection) for collection in collections]

            # Remove tags from notes.
            notes = re.sub(re_tag_pattern, "", notes)
            notes = re.sub(re_collection_pattern, "", notes)
            notes = notes.strip()

        else:

            notes = ""
            tags = []
            collections = []

        self._notes = notes
        self._tags = tags
        self._collections = collections

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
    def color(self):
        return self.data["color"]

    @property
    def books_collections(self):
        return self.data["books_collections"]

    @property
    def is_skipped(self):
        """ Skip annotations based on User Config. """

        color = self.data["color"]

        if color == 0 and self.appconfig["skip_color"]["underline"]:
            return True
        if color == 1 and self.appconfig["skip_color"]["green"]:
            return True
        if color == 2 and self.appconfig["skip_color"]["blue"]:
            return True
        if color == 3 and self.appconfig["skip_color"]["yellow"]:
            return True
        if color == 4 and self.appconfig["skip_color"]["pink"]:
            return True
        if color == 5 and self.appconfig["skip_color"]["purple"]:
            return True

        return False

    def to_dict(self):

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
                "is_protected": True,
                "in_trash": False,
            }
        }

        return data


class QueryAppleBooks:

    def __init__(self):

        self.bklibrary_sqlite = self._get_sqlite(path=AppDefaults.bklibrary_dir)
        self.aeannotation_sqlite = self._get_sqlite(path=AppDefaults.aeannotation_dir)

    def all_sources(self):

        data = self._execute_query(
            sqlite_file=self.bklibrary_sqlite,
            query=AppDefaults.source_query)

        return data

    def all_annotations(self):

        data = self._execute_query(
            sqlite_file=self.aeannotation_sqlite,
            query=AppDefaults.annotation_query)

        return data

    def _get_sqlite(self, path: pathlib.Path) -> pathlib.Path:
        """ Glob full database path.
        """
        sqlite_file = list(path.glob("*.sqlite"))

        try:
            sqlite_file = sqlite_file[0]
            return sqlite_file
        except IndexError:
            raise Exception(f"Couldn't find Apple Books database @ {path}. Exiting!")

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
            raise Exception(error)

        return None

    def _dict_factory(self, cursor: sqlite3.Cursor, row: tuple) -> dict:

        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]

        return d

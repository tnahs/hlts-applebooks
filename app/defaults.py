#!/usr/bin/env python3

from pathlib import Path
from datetime import datetime


home = Path.home()
date = datetime.now().strftime("%Y%m%d")


class AppDefaults:

    root_dir = home / ".bsync"

    config_file = root_dir / "config.json"

    day_dir = root_dir / date
    db_dir = day_dir / "db"
    json_dir = day_dir / "json"
    bklibrary_dir = db_dir / "BKLibrary"
    aeannotation_dir = db_dir / "AEAnnotation"

    annotation_query = """
        SELECT
            ZAEANNOTATION.ZANNOTATIONASSETID as source_id,
            ZANNOTATIONUUID as id,
            ZANNOTATIONSELECTEDTEXT as passage,
            ZANNOTATIONNOTE as notes,
            ZANNOTATIONSTYLE as color,
            ZANNOTATIONCREATIONDATE as created,
            ZANNOTATIONMODIFICATIONDATE as modified

        FROM ZAEANNOTATION

        WHERE ZANNOTATIONSELECTEDTEXT IS NOT NULL
            AND ZANNOTATIONDELETED = 0

        ORDER BY ZANNOTATIONASSETID;
    """

    source_query = """
        SELECT
            ZBKCOLLECTIONMEMBER.ZASSETID as id,
            ZBKLIBRARYASSET.ZTITLE as name,
            ZBKLIBRARYASSET.ZAUTHOR as author,
            ZBKCOLLECTION.ZTITLE as books_collection
        FROM ZBKCOLLECTIONMEMBER, ZBKLIBRARYASSET, ZBKCOLLECTION

        /*
        * "Books_Collection_ID" and "All_Collection_ID" are default
        * AppleBooks collections which include all books.
        */
        WHERE ZBKCOLLECTION.ZCOLLECTIONID IS NOT "Books_Collection_ID"
            AND ZBKCOLLECTION.ZCOLLECTIONID IS NOT "All_Collection_ID"
            AND ZBKCOLLECTIONMEMBER.ZCOLLECTION = ZBKCOLLECTION.Z_PK
            AND ZBKLIBRARYASSET.ZASSETID = ZBKCOLLECTIONMEMBER.ZASSETID

        ORDER BY ZBKLIBRARYASSET.ZTITLE;
    """


class AppleBooksDefaults:

    root = home / "Library/Containers/com.apple.iBooksX/Data/Documents"
    bklibrary_dir = root / "BKLibrary"
    aeannotation_dir = root / "AEAnnotation"

    ns_time_interval_since_1970 = 978307200.0
    origin = "apple_books"
    current_version = "Books v1.6 (1636.1)"


class ApiDefaults:

    url_verify = "/api/verify_api_key"
    url_refresh = "/api/import/refresh"
    url_add = "/api/import/add"

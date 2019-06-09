#!/usr/bin/env python3

from ..defaults import AppDefaults


class AppleBooksDefaults:

    # AppleBooks Data
    src_root_dir = AppDefaults.home / "Library/Containers/com.apple.iBooksX/Data/Documents"
    src_bklibrary_dir = src_root_dir / "BKLibrary"
    src_aeannotation_dir = src_root_dir / "AEAnnotation"

    # Local Data
    local_root_dir = AppDefaults.root_dir / "applebooks"
    local_day_dir = local_root_dir / AppDefaults.date
    local_db_dir = local_day_dir / "db"
    local_bklibrary_dir = local_db_dir / "BKLibrary"
    local_aeannotation_dir = local_db_dir / "AEAnnotation"

    # Misc
    origin = "apple_books"
    ns_time_interval_since_1970 = 978307200.0
    current_version = "Books v1.6 (1636.1)"

    # Queries
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

#!/usr/bin/env python3


def generate_dummy_annotations(count, id_prefix=""):

    data = []

    for num in range(count):

        data.append(
            {
                "id": f"ID-{id_prefix}-{num}",
                "passage": f"Testing {num}!",
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

    return data

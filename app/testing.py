#!/usr/bin/env python3


def generate_test_data(amount, offset=0):

    data = []

    for num in range(amount):

        data.append(
            {
                "id": f"ID-{num + offset}",
                "passage": f"Testing data #{num + offset}!",
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

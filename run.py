#!/usr/bin/env python3

import sys
import argparse

from app import App

"""
README: This works! Although the API response isn't great. It doesn't seem to
say when an annotation was added, just that it was "refreshed". Will be holding
off on any api-related updates until hlts_v2 is up and running.

To run with Books:
- Close Books
- Run: python3 run.py --setup
  This will build folder structure and config files.
- Set configuration in ~/.hltsync/config.json
- Run: python3 run.py applebooks
"""


parser = argparse.ArgumentParser()
parser.add_argument("reader",
                    choices=["dummy", "applebooks", "kindle"],
                    nargs="?",
                    help="Which reader to sync.")
parser.add_argument("-s","--setup",
                    action="store_true",
                    help="Run initial setup.")

args = parser.parse_args()


if __name__ == "__main__":

    app = App(args)

    if args.setup:
        sys.exit()

    app.run()
    sys.exit()

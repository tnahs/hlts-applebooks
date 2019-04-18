#!/usr/bin/env python3

from app import App
from app.tools import applebooks_running


app = App()


if __name__ == "__main__":

    if not applebooks_running():
        app.run()
    else:
        raise Exception("Apple Books currently running.")

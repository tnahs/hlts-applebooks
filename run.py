#!/usr/bin/env python3

import sys

from app import App


app = App(debug=True)


if __name__ == "__main__":

    app.run()
    sys.exit()

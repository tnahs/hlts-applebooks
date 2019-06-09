#!/usr/bin/env python3

from pathlib import Path
from datetime import datetime


class AppDefaults:

    home = Path.home()
    date = datetime.now().strftime("%Y-%m-%d")

    name = "hltsync"
    name_pretty = "HL+Sync"

    root_dir = home / ".hltsync"
    config_file = root_dir / "config.json"
    log_file = root_dir / "app.log"

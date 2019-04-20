#!/usr/bin/env python3

import os
import sys
import shutil
import pathlib
import psutil
from typing import Union


def applebooks_running() -> bool:

    for proc in psutil.process_iter():

        try:
            pinfo = proc.as_dict(attrs=["name"])
        except psutil.NoSuchProcess:
            """ When a process doesn't have a name it might mean it's a zombie
            process which ends up raising a NoSuchProcess exception or its
            subclass the ZombieProcess exception.
            """
            pass
        except Exception as error:
            raise Exception(error)

        if pinfo["name"] == "Books":
            return True

    return False


class OSTools:
    """ TODO: Be more explicit with the Exceptions here..."""

    def delete_dir(self, path: pathlib.PosixPath) -> None:

        try:
            shutil.rmtree(path)
        except OSError:
            pass
        except Exception as error:
            raise Exception(error)

    def make_dir(self, path: pathlib.PosixPath) -> None:

        try:
            os.makedirs(path)
        except FileExistsError:
            pass
        except OSError as error:
            raise Exception(f"{error.filename} - {error.strerror}")
        except Exception as error:
            raise Exception(error)

    def copy_dir(self, src: pathlib.PosixPath,
                 dest: pathlib.PosixPath) -> None:

        try:
            shutil.copytree(src, dest)
        except OSError as error:
            raise Exception(f"{error.filename} - {error.strerror}")
        except Exception as error:
            raise Exception(error)


def to_lower(input_: Union[list, str, dict]) -> Union[list, str, dict]:

    if type(input_) is str:
        return input_.lower()

    elif type(input_) is list:
        return [v.lower() for v in input_]

    elif type(input_) is dict:
        return dict((k, v.lower()) for k, v in input_.items())


def print_progress_bar(current_iteration, total_iteration, max_bar=50):
    """ TODO: Clean this up. Both how it looks and how its implemented
    inside of a loop.

    Call in a loop to create terminal progress bar
    """

    completed_percent = f"{100 * (current_iteration / float(total_iteration)):.1f}"
    completed_bar = int(round(max_bar * current_iteration / float(total_iteration)))

    bar = f"{'▓' * completed_bar}{'░' * (max_bar - completed_bar)}"

    sys.stdout.write(f"\r{bar} {completed_percent}%"),

    if current_iteration == total_iteration:
        sys.stdout.write("\n")

    sys.stdout.flush()

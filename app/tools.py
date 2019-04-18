#!/usr/bin/env python3

import os
import shutil
import pathlib
import psutil
from typing import Union


def applebooks_running() -> bool:

    for proc in psutil.process_iter():

        try:
            pinfo = proc.as_dict(attrs=["name"])
        except psutil.NoSuchProcess:
            pass
        except Exception as error:
            print(error)

        if pinfo["name"] == "Books":
            return True

    return False


class OSTools:

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

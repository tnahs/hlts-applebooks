#!/usr/bin/env python3

from ..errors import ApplicationError


class ApiError(ApplicationError):
    def __init__(self, message, app=None):
        super().__init__(message, app)

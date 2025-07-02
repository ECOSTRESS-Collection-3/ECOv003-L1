from __future__ import annotations
# Various exception classes that we want to report


class VicarRunError(Exception):
    """Class thrown in VICAR process either returns a nonzero return value
    or a failed status message."""

    def __init__(self, message: str) -> None:
        self.message = message

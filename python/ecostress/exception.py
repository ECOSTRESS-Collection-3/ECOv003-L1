# Various exception classes that we want to report


class VicarRunException(Exception):
    """Class thrown in VICAR process either returns a nonzero return value
    or a failed status message."""

    def __init__(self, message):
        self.message = message

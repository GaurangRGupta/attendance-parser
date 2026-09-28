"""Errors raised while parsing or rendering an attendance report."""


class AttendanceError(Exception):
    """Base error for this package."""


class ParseError(AttendanceError):
    """The detailed attendance PDF could not be read or did not match the expected layout."""

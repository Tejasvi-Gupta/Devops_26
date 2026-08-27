"""
Minimal semantic version comparison, dependency-free (avoids requiring
`packaging` just for this one thing on a student's fresh machine).

Handles the common case: "3.11.4" >= "3.11.0". Doesn't handle pre-release
tags (e.g. "3.11.0-beta") -- if that shows up, it's treated as unparseable
and reported honestly rather than guessed at.
"""
import re


def parse_version(version_str: str) -> tuple[int, ...] | None:
    """'3.11.4' -> (3, 11, 4). Returns None if it doesn't look like a
    plain dotted-numeric version."""
    if not version_str:
        return None
    if not re.fullmatch(r"\d+(\.\d+)*", version_str.strip()):
        return None
    return tuple(int(part) for part in version_str.strip().split("."))


def meets_minimum(found_version: str | None, min_version: str) -> bool | None:
    """
    Returns True if found_version >= min_version, False if it's below,
    or None if either version string couldn't be parsed (caller should
    treat None as 'unknown, report as error' rather than pass/fail it).
    """
    if found_version is None:
        return False

    found = parse_version(found_version)
    minimum = parse_version(min_version)
    if found is None or minimum is None:
        return None

    # Pad the shorter tuple with zeros so (3, 11) compares correctly
    # against (3, 11, 4).
    length = max(len(found), len(minimum))
    found_padded = found + (0,) * (length - len(found))
    minimum_padded = minimum + (0,) * (length - len(minimum))

    return found_padded >= minimum_padded

#!/usr/bin/env python3
"""Generate a compact JSON summary from a profile object."""

import json
import re
import sys


INTEGER_RE = re.compile(r"(?:0|[1-9][0-9]*)\Z")


class InvalidJSON(ValueError):
    pass


class IntegerToken:
    def __init__(self, token):
        self.token = token


def fail(message):
    sys.stderr.buffer.write((message + "\n").encode("utf-8"))
    return 2


def enable_unlimited_decimal_conversion():
    setter = getattr(sys, "set_int_max_str_digits", None)
    if setter is not None:
        setter(0)


def reject_constant(token):
    raise InvalidJSON(f"non-standard JSON constant: {token}")


def reject_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise InvalidJSON("duplicate object key")
        result[key] = value
    return result


def main(argv):
    enable_unlimited_decimal_conversion()

    if len(argv) != 2:
        return fail("ERROR: usage: tool.py input.json")

    filename = argv[1]
    if "/" in filename or "\\" in filename:
        return fail("ERROR: input file not found")
    try:
        with open(filename, "rb") as source:
            data = source.read()
    except OSError:
        return fail("ERROR: input file not found")

    try:
        if data.startswith(b"\xef\xbb\xbf"):
            raise InvalidJSON("BOM is not allowed")
        text = data.decode("utf-8")
        profile = json.loads(
            text,
            object_pairs_hook=reject_duplicate_keys,
            parse_int=IntegerToken,
            parse_constant=reject_constant,
        )
        if not isinstance(profile, dict):
            raise InvalidJSON("top level is not an object")
        if not all(key in profile for key in ("name", "age", "skills")):
            raise InvalidJSON("missing required field")

        name = profile["name"]
        age_token = profile["age"]
        skills = profile["skills"]
        if not isinstance(name, str) or name == "":
            raise InvalidJSON("invalid name")
        if not isinstance(age_token, IntegerToken) or INTEGER_RE.fullmatch(age_token.token) is None:
            raise InvalidJSON("invalid age")
        if not isinstance(skills, list) or any(not isinstance(skill, str) for skill in skills):
            raise InvalidJSON("invalid skills")
        age = int(age_token.token)
    except (UnicodeDecodeError, json.JSONDecodeError, InvalidJSON, ValueError, TypeError):
        return fail("ERROR: invalid JSON data")

    output = {"name": name, "age": age, "skill_count": len(skills)}
    encoded = json.dumps(output, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + "\n"
    sys.stdout.buffer.write(encoded.encode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

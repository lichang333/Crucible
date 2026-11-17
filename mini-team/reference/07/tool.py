#!/usr/bin/env python3
"""Deduplicate JSONL records by id, retaining each id's last value."""

import json
import sys


class InvalidJSONL(ValueError):
    pass


def fail(message):
    sys.stderr.buffer.write((message + "\n").encode("utf-8"))
    return 2


def enable_unlimited_decimal_conversion():
    setter = getattr(sys, "set_int_max_str_digits", None)
    if setter is not None:
        setter(0)


def reject_constant(token):
    raise InvalidJSONL(f"non-standard JSON constant: {token}")


def reject_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise InvalidJSONL("duplicate object key")
        result[key] = value
    return result


def split_lines(text):
    if text == "":
        return []
    parts = text.split("\n")
    ended_with_lf = text.endswith("\n")
    if ended_with_lf:
        parts.pop()
    lines = []
    for index, line in enumerate(parts):
        terminated = index < len(parts) - 1 or ended_with_lf
        if terminated and line.endswith("\r"):
            line = line[:-1]
        lines.append(line)
    return lines


def main(argv):
    enable_unlimited_decimal_conversion()

    if len(argv) != 2:
        return fail("ERROR: usage: tool.py records.jsonl")

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
            raise InvalidJSONL("BOM is not allowed")
        text = data.decode("utf-8")
        latest = {}
        for line in split_lines(text):
            if line == "":
                raise InvalidJSONL("blank line")
            record = json.loads(
                line,
                object_pairs_hook=reject_duplicate_keys,
                parse_constant=reject_constant,
            )
            if not isinstance(record, dict) or "id" not in record or "value" not in record:
                raise InvalidJSONL("record must contain id and value")
            record_id = record["id"]
            if not isinstance(record_id, str) or record_id == "":
                raise InvalidJSONL("invalid id")
            latest[record_id] = record["value"]
    except (UnicodeDecodeError, json.JSONDecodeError, InvalidJSONL, ValueError, TypeError):
        return fail("ERROR: invalid JSONL")

    output_lines = []
    for record_id in sorted(latest):
        output_lines.append(
            json.dumps(
                {"value": latest[record_id], "id": record_id},
                ensure_ascii=False,
                separators=(",", ":"),
            )
        )
    output = "".join(line + "\n" for line in output_lines)
    sys.stdout.buffer.write(output.encode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

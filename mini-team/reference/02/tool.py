#!/usr/bin/env python3
"""Filter CSV score records while enforcing the task's strict CSV dialect."""

import re
import sys


INTEGER_RE = re.compile(r"(?:0|[1-9][0-9]*)\Z")


def fail(message):
    sys.stderr.buffer.write((message + "\n").encode("utf-8"))
    return 2


def enable_unlimited_decimal_conversion():
    setter = getattr(sys, "set_int_max_str_digits", None)
    if setter is not None:
        setter(0)


def split_physical_lines(text):
    if not text:
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
        if "\r" in line:
            raise ValueError("isolated carriage return")
        lines.append(line)
    return lines


def parse_csv_record(line):
    fields = []
    index = 0
    length = len(line)

    while True:
        if index < length and line[index] == '"':
            index += 1
            value = []
            closed = False
            while index < length:
                char = line[index]
                if char == '"':
                    if index + 1 < length and line[index + 1] == '"':
                        value.append('"')
                        index += 2
                    else:
                        index += 1
                        closed = True
                        break
                else:
                    value.append(char)
                    index += 1
            if not closed:
                raise ValueError("unclosed quoted field")
            fields.append("".join(value))
            if index < length and line[index] != ",":
                raise ValueError("characters after closing quote")
        else:
            start = index
            while index < length and line[index] != ",":
                if line[index] == '"':
                    raise ValueError("quote in unquoted field")
                index += 1
            fields.append(line[start:index])

        if index == length:
            break
        index += 1  # comma

    return fields


def quote_field(value):
    if any(char in value for char in (",", '"', "\r", "\n")):
        return '"' + value.replace('"', '""') + '"'
    return value


def main(argv):
    enable_unlimited_decimal_conversion()

    if len(argv) != 3:
        return fail("ERROR: usage: tool.py input.csv minimum_score")

    minimum_text = argv[2]
    if INTEGER_RE.fullmatch(minimum_text) is None:
        return fail("ERROR: invalid minimum_score")
    minimum_score = int(minimum_text)

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
            raise ValueError("BOM is not allowed")
        text = data.decode("utf-8")
        lines = split_physical_lines(text)
        if not lines:
            raise ValueError("missing header")
        if any(line == "" for line in lines):
            raise ValueError("blank record")

        records = [parse_csv_record(line) for line in lines]
        if records[0] != ["name", "score", "class"]:
            raise ValueError("invalid header")

        selected = []
        for row in records[1:]:
            if len(row) != 3:
                raise ValueError("wrong field count")
            score_text = row[1]
            if INTEGER_RE.fullmatch(score_text) is None:
                raise ValueError("invalid score")
            score = int(score_text)
            if score >= minimum_score:
                selected.append((row[0], str(score), row[2]))
    except (UnicodeDecodeError, ValueError):
        return fail("ERROR: invalid CSV")

    output_rows = [["name", "score", "class"]]
    output_rows.extend(selected)
    output = "".join(",".join(quote_field(field) for field in row) + "\n" for row in output_rows)
    sys.stdout.buffer.write(output.encode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

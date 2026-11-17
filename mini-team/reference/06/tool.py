#!/usr/bin/env python3
"""Count valid log records by their level field."""

import re
import sys
from datetime import date


DATE_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}\Z")
TIME_RE = re.compile(r"(?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]\Z")
LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")


def fail(message):
    sys.stderr.buffer.write((message + "\n").encode("utf-8"))
    return 2


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


def valid_date(text):
    if DATE_RE.fullmatch(text) is None:
        return False
    try:
        date.fromisoformat(text)
    except ValueError:
        return False
    return True


def valid_record(line):
    if len(line) < 21 or line[10] != " " or line[19] != " ":
        return None

    date_text = line[:10]
    time_text = line[11:19]
    if not valid_date(date_text) or TIME_RE.fullmatch(time_text) is None:
        return None

    message_separator = line.find(" ", 20)
    if message_separator < 0:
        return None
    level = line[20:message_separator]
    message = line[message_separator + 1 :]
    if level not in LEVELS or "\r" in message or "\n" in message:
        return None
    if not any(not char.isspace() for char in message):
        return None
    return level


def main(argv):
    if len(argv) != 2:
        return fail("ERROR: usage: tool.py application.log")

    filename = argv[1]
    if "/" in filename or "\\" in filename:
        return fail("ERROR: input file not found")
    try:
        with open(filename, "rb") as source:
            data = source.read()
    except OSError:
        return fail("ERROR: input file not found")

    try:
        text = data.decode("utf-8")
        lines = split_lines(text)
        counts = dict.fromkeys(LEVELS, 0)
        for line in lines:
            level = valid_record(line)
            if level is None:
                raise ValueError("invalid log record")
            counts[level] += 1
    except (UnicodeDecodeError, ValueError):
        return fail("ERROR: invalid log file")

    output = "".join(f"{level} {counts[level]}\n" for level in LEVELS)
    sys.stdout.buffer.write(output.encode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

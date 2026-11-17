#!/usr/bin/env python3
"""Aggregate inventory deltas by item code."""

import re
import sys


ITEM_RE = re.compile(r"[A-Z0-9]+\Z")
QUANTITY_RE = re.compile(r"(?:0|[1-9][0-9]*|-[1-9][0-9]*)\Z")


def fail(message):
    sys.stderr.buffer.write((message + "\n").encode("utf-8"))
    return 2


def enable_unlimited_decimal_conversion():
    setter = getattr(sys, "set_int_max_str_digits", None)
    if setter is not None:
        setter(0)


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
        return fail("ERROR: usage: tool.py inventory.txt")

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
        totals = {}
        for line in lines:
            if line == "" or line.count(",") != 1:
                raise ValueError("invalid record")
            item, quantity_text = line.split(",")
            if ITEM_RE.fullmatch(item) is None or QUANTITY_RE.fullmatch(quantity_text) is None:
                raise ValueError("invalid item or quantity")
            totals[item] = totals.get(item, 0) + int(quantity_text)
    except (UnicodeDecodeError, ValueError):
        return fail("ERROR: invalid inventory data")

    output = "".join(f"{item},{totals[item]}\n" for item in sorted(totals))
    sys.stdout.buffer.write(output.encode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

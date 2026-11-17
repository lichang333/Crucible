#!/usr/bin/env python3
"""Calculate the number of calendar days between two Gregorian dates."""

import re
import sys
from datetime import date


DATE_PATTERN = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")


def parse_date(value):
    if DATE_PATTERN.fullmatch(value) is None:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def main(argv):
    if len(argv) != 3:
        sys.stderr.write("ERROR: usage: tool.py start_date end_date\n")
        return 2

    start_date = parse_date(argv[1])
    end_date = parse_date(argv[2])
    if start_date is None or end_date is None:
        sys.stderr.write("ERROR: invalid date\n")
        return 2

    if start_date > end_date:
        sys.stderr.write("ERROR: start_date must not be after end_date\n")
        return 2

    sys.stdout.write(f"{(end_date - start_date).days}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

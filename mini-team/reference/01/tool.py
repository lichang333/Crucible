#!/usr/bin/env python3
"""Count case-insensitive Unicode-whitespace-separated words."""

import sys


def fail(message):
    sys.stderr.buffer.write((message + "\n").encode("utf-8"))
    return 2


def main(argv):
    if len(argv) != 2:
        return fail("ERROR: usage: tool.py words.txt")

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
    except UnicodeDecodeError:
        return fail("ERROR: invalid text")

    counts = {}
    for word in text.split():
        lowered = word.lower()
        counts[lowered] = counts.get(lowered, 0) + 1

    lines = [f"{word} {count}\n" for word, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))]
    sys.stdout.buffer.write("".join(lines).encode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

#!/usr/bin/env python3
"""Count filename extensions without opening the listed paths."""

import sys


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


def extension_for(filename):
    dot = filename.rfind(".")
    if dot <= 0 or dot == len(filename) - 1:
        return "(none)"
    return filename[dot + 1 :].lower()


def main(argv):
    if len(argv) != 2:
        return fail("ERROR: usage: tool.py filenames.txt")

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
        names = split_lines(text)
        if any(name == "" or "/" in name or "\\" in name for name in names):
            raise ValueError("invalid filename line")
    except (UnicodeDecodeError, ValueError):
        return fail("ERROR: invalid filename list")

    counts = {}
    for name in names:
        extension = extension_for(name)
        counts[extension] = counts.get(extension, 0) + 1

    output = "".join(f"{extension} {counts[extension]}\n" for extension in sorted(counts))
    sys.stdout.buffer.write(output.encode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

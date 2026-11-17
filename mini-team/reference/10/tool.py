#!/usr/bin/env python3
"""Merge two restricted INI files with deterministic ordering."""

import sys


class InvalidINI(ValueError):
    pass


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


def parse_ini(text):
    sections = {}
    seen_sections = set()
    current_section = None

    for original_line in split_lines(text):
        if original_line.strip() == "":
            continue
        left_trimmed = original_line.lstrip()
        if left_trimmed.startswith("#") or left_trimmed.startswith(";"):
            continue

        line = original_line.strip()
        if line.startswith("[") and line.endswith("]"):
            section_name = line[1:-1].strip()
            if not section_name or "[" in section_name or "]" in section_name:
                raise InvalidINI("invalid section name")
            if section_name in seen_sections:
                raise InvalidINI("duplicate section")
            seen_sections.add(section_name)
            sections[section_name] = {}
            current_section = section_name
            continue

        if current_section is None:
            raise InvalidINI("key outside a section")
        separator = line.find("=")
        if separator < 0:
            raise InvalidINI("unrecognized line")
        key = line[:separator].strip()
        value = line[separator + 1 :].strip()
        if key == "":
            raise InvalidINI("empty key")
        if key in sections[current_section]:
            raise InvalidINI("duplicate key")
        sections[current_section][key] = value

    return sections


def check_filename(filename):
    if "/" in filename or "\\" in filename:
        return False
    try:
        with open(filename, "rb"):
            return True
    except OSError:
        return False


def read_and_parse(filename):
    try:
        with open(filename, "rb") as source:
            data = source.read()
        if data.startswith(b"\xef\xbb\xbf"):
            raise InvalidINI("BOM is not allowed")
        text = data.decode("utf-8")
        return parse_ini(text)
    except (OSError, UnicodeDecodeError, InvalidINI) as error:
        raise InvalidINI("invalid INI file") from error


def main(argv):
    if len(argv) != 3:
        return fail("ERROR: usage: tool.py defaults.ini overrides.ini")

    defaults_filename, overrides_filename = argv[1], argv[2]
    for filename in (defaults_filename, overrides_filename):
        if "/" in filename or "\\" in filename:
            return fail("ERROR: input file not found")
        try:
            with open(filename, "rb"):
                pass
        except OSError:
            return fail("ERROR: input file not found")

    try:
        defaults = read_and_parse(defaults_filename)
        overrides = read_and_parse(overrides_filename)
    except InvalidINI:
        return fail("ERROR: invalid INI file")

    merged = {}
    for source in (defaults, overrides):
        for section_name, values in source.items():
            merged.setdefault(section_name, {}).update(values)

    blocks = []
    for section_name in sorted(merged):
        values = merged[section_name]
        if not values:
            continue
        block = [f"[{section_name}]\n"]
        block.extend(f"{key}={values[key]}\n" for key in sorted(values))
        blocks.append("".join(block))

    output = "\n".join(blocks)
    sys.stdout.buffer.write(output.encode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

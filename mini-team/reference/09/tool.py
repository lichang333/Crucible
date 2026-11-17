#!/usr/bin/env python3
"""Select and sort incomplete tasks that are due by a reference date."""

import json
import re
import sys
from datetime import date


DATE_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}\Z")


class InvalidTaskData(ValueError):
    pass


def fail(message):
    sys.stderr.buffer.write((message + "\n").encode("utf-8"))
    return 2


def enable_unlimited_decimal_conversion():
    setter = getattr(sys, "set_int_max_str_digits", None)
    if setter is not None:
        setter(0)


def reject_constant(token):
    raise InvalidTaskData(f"non-standard JSON constant: {token}")


def reject_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise InvalidTaskData("duplicate object key")
        result[key] = value
    return result


def parse_date(text):
    if not isinstance(text, str) or DATE_RE.fullmatch(text) is None:
        raise InvalidTaskData("invalid date format")
    try:
        return date.fromisoformat(text)
    except ValueError as error:
        raise InvalidTaskData("invalid Gregorian date") from error


def main(argv):
    enable_unlimited_decimal_conversion()

    if len(argv) != 3:
        return fail("ERROR: usage: tool.py tasks.json reference_date")

    reference_text = argv[2]
    try:
        reference_date = parse_date(reference_text)
    except InvalidTaskData:
        return fail("ERROR: invalid reference_date")

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
            raise InvalidTaskData("BOM is not allowed")
        text = data.decode("utf-8")
        tasks = json.loads(
            text,
            object_pairs_hook=reject_duplicate_keys,
            parse_constant=reject_constant,
        )
        if not isinstance(tasks, list):
            raise InvalidTaskData("top level is not an array")

        seen_ids = set()
        validated = []
        for task in tasks:
            if not isinstance(task, dict):
                raise InvalidTaskData("task is not an object")
            if not all(key in task for key in ("id", "title", "due_date", "done")):
                raise InvalidTaskData("missing task field")

            task_id = task["id"]
            title = task["title"]
            due_date_text = task["due_date"]
            done = task["done"]
            if type(task_id) is not int or task_id <= 0:
                raise InvalidTaskData("invalid task id")
            if task_id in seen_ids:
                raise InvalidTaskData("duplicate task id")
            seen_ids.add(task_id)
            if not isinstance(title, str) or title == "":
                raise InvalidTaskData("invalid title")
            due_date = parse_date(due_date_text)
            if type(done) is not bool:
                raise InvalidTaskData("invalid done value")
            validated.append((task_id, title, due_date_text, due_date, done))
    except (UnicodeDecodeError, json.JSONDecodeError, InvalidTaskData, ValueError, TypeError):
        return fail("ERROR: invalid task data")

    selected = [
        item
        for item in validated
        if not item[4] and item[3] <= reference_date
    ]
    selected.sort(key=lambda item: (item[3], item[0]))
    output_lines = [
        json.dumps(
            {"id": task_id, "title": title, "due_date": due_date_text},
            ensure_ascii=False,
            separators=(",", ":"),
        )
        for task_id, title, due_date_text, _due_date, _done in selected
    ]
    output = "".join(line + "\n" for line in output_lines)
    sys.stdout.buffer.write(output.encode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

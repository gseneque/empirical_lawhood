# SPDX-License-Identifier: MPL-2.0
"""Separate CIF lexical state machine for original/export assessment.

This reader shares no parser or assembly routines with the producer. It accepts
the one-data-block CIF syntax used by the selected originals and refuses extra
blocks, duplicate items/categories and incomplete loops rather than guessing.
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class _Token:
    value: str
    bare: bool


def _tokens(text):
    if type(text) is not str:
        raise ValueError("independent CIF input must be text")
    cursor = 0
    size = len(text)
    while cursor < size:
        if text[cursor].isspace():
            cursor += 1
            continue
        if text[cursor] == "#":
            end = text.find("\n", cursor)
            cursor = size if end < 0 else end + 1
            continue
        if text[cursor] == ";" and (cursor == 0 or text[cursor - 1] == "\n"):
            start = cursor + 1
            end = text.find("\n;", start)
            if end < 0:
                raise ValueError("independent CIF unterminated text field")
            after = end + 2
            if after < size and text[after] not in "\r\n":
                raise ValueError("independent CIF malformed text delimiter")
            yield _Token(text[start:end], False)
            cursor = after
            continue
        if text[cursor] in "'\"":
            quote = text[cursor]
            start = cursor + 1
            cursor = start
            while cursor < size:
                if text[cursor] == quote and (
                    cursor + 1 == size or text[cursor + 1].isspace()
                ):
                    break
                if text[cursor] in "\r\n":
                    raise ValueError("independent CIF multiline quoted field")
                cursor += 1
            if cursor == size:
                raise ValueError("independent CIF unterminated quoted field")
            yield _Token(text[start:cursor], False)
            cursor += 1
            continue
        start = cursor
        while cursor < size and not text[cursor].isspace():
            cursor += 1
        yield _Token(text[start:cursor], True)


def read_cif(text):
    """Read complete category rows, keeping every source token as text."""
    tokens = list(_tokens(text))
    if not tokens or not tokens[0].bare or not tokens[0].value.startswith("data_"):
        raise ValueError("independent CIF missing data block")
    categories = {}
    cursor = 1

    def control(token):
        return token.bare and (
            token.value.startswith(("_", "data_", "save_"))
            or token.value in ("loop_", "stop_", "global_")
        )

    while cursor < len(tokens):
        token = tokens[cursor]
        if token.bare and token.value == "loop_":
            cursor += 1
            headers = []
            while cursor < len(tokens) and tokens[cursor].bare and tokens[cursor].value.startswith("_"):
                headers.append(tokens[cursor].value)
                cursor += 1
            if not headers or len(set(headers)) != len(headers):
                raise ValueError("independent CIF invalid loop headers")
            if any("." not in name for name in headers):
                raise ValueError("independent CIF category/item separator missing")
            category = headers[0].split(".", 1)[0]
            if category in categories or any(name.split(".", 1)[0] != category for name in headers):
                raise ValueError("independent CIF duplicate or mixed category")
            values = []
            while cursor < len(tokens) and not control(tokens[cursor]):
                values.append(tokens[cursor].value)
                cursor += 1
            if len(values) % len(headers):
                raise ValueError("independent CIF incomplete loop row")
            names = [name.split(".", 1)[1] for name in headers]
            categories[category] = [
                dict(zip(names, values[offset:offset + len(names)], strict=True))
                for offset in range(0, len(values), len(names))
            ]
        elif token.bare and token.value.startswith("_") and "." in token.value:
            category, name = token.value.split(".", 1)
            cursor += 1
            if cursor == len(tokens) or control(tokens[cursor]):
                raise ValueError("independent CIF missing scalar value")
            rows = categories.setdefault(category, [{}])
            if len(rows) != 1 or name in rows[0]:
                raise ValueError("independent CIF duplicate scalar item")
            rows[0][name] = tokens[cursor].value
            cursor += 1
        else:
            raise ValueError("independent CIF unsupported extra block/control")
    return categories

#!/usr/bin/env python3
"""Deterministically validate the public Bergen Moske timetable JSON."""

from __future__ import annotations

import calendar
import datetime as dt
import json
import re
import sys
from pathlib import Path
from typing import Any


SOURCE_PAGE = "https://www.facebook.com/Bergenmoske.no/"
TIME_KEYS = ("fajr", "sunrise", "dhohr", "asr", "magrib", "isha")
TOP_KEYS = {
    "schema_version",
    "mosque",
    "location",
    "timezone",
    "year",
    "month",
    "month_name",
    "source_page",
    "source_post",
    "source_photo_id",
    "source_caption",
    "published_at",
    "verified_at",
    "days",
}
DAY_KEYS = {"date", *TIME_KEYS}
TIME_RE = re.compile(r"(?:[01]\d|2[0-3]):[0-5]\d")
PHOTO_ID_RE = re.compile(r"[1-9]\d*")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def parse_timestamp(value: Any, field: str) -> dt.datetime:
    require(isinstance(value, str) and value.strip() == value, f"{field} must be a trimmed ISO timestamp")
    try:
        parsed = dt.datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field} must be a valid ISO timestamp") from exc
    require(parsed.tzinfo is not None and parsed.utcoffset() is not None, f"{field} must include a UTC offset")
    return parsed


def minutes(value: str) -> int:
    hour, minute = value.split(":")
    return int(hour) * 60 + int(minute)


def validate(data: Any) -> None:
    require(isinstance(data, dict), "top level must be an object")
    require(set(data) == TOP_KEYS, "top-level fields do not match the schema")
    require(data["schema_version"] == 1, "schema_version must be 1")
    require(data["mosque"] == "Bergen Moske", "mosque must be Bergen Moske")
    require(data["location"] == "Bergen", "location must be Bergen")
    require(data["timezone"] == "Europe/Oslo", "timezone must be Europe/Oslo")

    year = data["year"]
    month = data["month"]
    require(isinstance(year, int) and not isinstance(year, bool) and 2000 <= year <= 2100, "year is invalid")
    require(isinstance(month, int) and not isinstance(month, bool) and 1 <= month <= 12, "month is invalid")
    require(data["month_name"] == calendar.month_name[month], "month_name does not match month")
    require(data["source_page"] == SOURCE_PAGE, "source_page is not the official Bergen Moske page")
    require(
        isinstance(data["source_post"], str)
        and data["source_post"].startswith("https://www.facebook.com/Bergenmoske.no/"),
        "source_post must belong to the official Bergen Moske page",
    )
    require(
        isinstance(data["source_photo_id"], str)
        and PHOTO_ID_RE.fullmatch(data["source_photo_id"]) is not None,
        "source_photo_id must be a positive decimal identifier string",
    )
    caption = data["source_caption"]
    require(isinstance(caption, str) and caption.strip() == caption and caption, "source_caption must be non-empty and trimmed")
    require(calendar.month_name[month].casefold() in caption.casefold(), "source_caption must name the timetable month")
    parse_timestamp(data["published_at"], "published_at")
    parse_timestamp(data["verified_at"], "verified_at")

    days = data["days"]
    expected_count = calendar.monthrange(year, month)[1]
    require(isinstance(days, list), "days must be an array")
    require(len(days) == expected_count, f"days must contain exactly {expected_count} rows")

    for index, row in enumerate(days, start=1):
        expected_date = dt.date(year, month, index).isoformat()
        require(isinstance(row, dict) and set(row) == DAY_KEYS, f"row {index} fields do not match the schema")
        require(row["date"] == expected_date, f"row {index} date must be {expected_date}")
        values = []
        for key in TIME_KEYS:
            value = row[key]
            require(isinstance(value, str) and TIME_RE.fullmatch(value) is not None, f"{expected_date} {key} must be strict HH:MM")
            values.append(minutes(value))
        require(all(a < b for a, b in zip(values, values[1:])), f"{expected_date} times must be strictly chronological")


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) == 2 else Path("current.json")
    require(len(sys.argv) <= 2, "usage: validate.py [current.json]")
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    validate(data)
    print(f"VALID: {path}")


if __name__ == "__main__":
    try:
        main()
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        raise SystemExit(1)

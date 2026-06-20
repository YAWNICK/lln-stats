"""Shared normalization helpers for all extractors."""

from __future__ import annotations

import re
from typing import Any

import pandas as pd

from lln_stats.schema import RESULT_COLUMNS

ROMAN_TO_INT = {
    "I": 1,
    "II": 2,
    "III": 3,
    "IV": 4,
    "V": 5,
    "VI": 6,
    "VII": 7,
    "VIII": 8,
    "IX": 9,
    "X": 10,
    "XI": 11,
    "XII": 12,
    "XIII": 13,
    "XIV": 14,
    "XV": 15,
    "XVI": 16,
    "XVII": 17,
    "XVIII": 18,
    "XIX": 19,
    "XX": 20,
}

STATUS_ALIASES = {
    "a": "dnf",
    "aufg": "dnf",
    "aufg.": "dnf",
    "dnf": "dnf",
    "b": "dns",
    "ab": "dns",
    "ab.": "dns",
    "abg": "dns",
    "abg.": "dns",
    "n.a": "dns",
    "n.a.": "dns",
    "dns": "dns",
    "disq": "dq",
    "disq.": "dq",
    "dq": "dq",
}

EVENT_CODE_MAP = {
    "L800": "800m",
    "L1K0": "1000m",
    "L1K5": "1500m",
    "L3K0": "3000m",
    "L5K0": "5000m",
    "H3K0": "3000m Hindernis",
    "H3K0_0762": "3000m Hindernis 0.762m",
    "H3K0_0914": "3000m Hindernis 0.914m",
}


def clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = re.sub(r"\s+", " ", str(value).replace("\xa0", " ")).strip()
    return text or None


def parse_int(value: Any) -> int | None:
    text = clean_text(value)
    if not text:
        return None
    match = re.search(r"\d+", text)
    return int(match.group()) if match else None


def parse_result_mark(mark: Any) -> tuple[int | None, int | None]:
    text = clean_text(mark)
    if not text:
        return None, None
    text = text.replace(" ", "")
    match = re.match(r"(?P<rank>\d+|-)?\.?/(?P<heat>[IVXLCDM]+|\d+)", text)
    if not match:
        return None, None
    rank = int(match.group("rank")) if match.group("rank") and match.group("rank") != "-" else None
    heat_text = match.group("heat")
    heat = int(heat_text) if heat_text.isdigit() else ROMAN_TO_INT.get(heat_text)
    return rank, heat


def normalize_event(value: Any) -> str | None:
    text = clean_text(value)
    if not text:
        return None
    text = text.replace("1.000", "1000").replace("1.500", "1500").replace("3.000", "3000")
    text = text.replace("5.000", "5000")
    text = re.sub(r"\s+", " ", text)
    if "Hindernis" in text:
        height_match = re.search(r"(0[,.]\d{3})\s*m", text)
        height = f" {height_match.group(1).replace(',', '.')}m" if height_match else ""
        distance = re.search(r"(\d{3,4})\s*m", text)
        return f"{distance.group(1)}m Hindernis{height}" if distance else f"Hindernis{height}".strip()
    match = re.search(r"(\d{3,4})\s*m", text)
    return f"{match.group(1)}m" if match else text


def normalize_event_code(code: Any) -> str | None:
    text = clean_text(code)
    if not text:
        return None
    if text in EVENT_CODE_MAP:
        return EVENT_CODE_MAP[text]
    base = text.split("_", 1)[0]
    return EVENT_CODE_MAP.get(base, text)


def parse_gender(value: Any) -> str | None:
    text = clean_text(value)
    if not text:
        return None
    lower = text.lower()
    if re.search(r"\b(w|weiblich|frauen|wju|w\d|kinder w|jugend w)\b", lower):
        return "W"
    if re.search(r"\b(m|männlich|maennlich|männer|maenner|mju|m\d|kinder m|jugend m)\b", lower):
        return "M"
    if text in {"M", "W"}:
        return text
    return None


def parse_time_seconds(value: Any) -> float | None:
    text = clean_text(value)
    if not text:
        return None
    text = re.sub(r"\s*\([^)]*\)", "", text)
    text = text.replace(",", ".")
    if not re.fullmatch(r"\d+(?::\d{1,2}){0,2}(?:\.\d+)?", text):
        return None
    parts = text.split(":")
    if len(parts) == 1:
        return float(parts[0])
    seconds = float(parts[-1])
    minutes = int(parts[-2])
    hours = int(parts[-3]) if len(parts) == 3 else 0
    return hours * 3600 + minutes * 60 + seconds


def normalize_status(value: Any) -> str:
    text = clean_text(value)
    if not text:
        return "unknown"
    lowered = text.lower().strip()
    lowered = re.sub(r"\s*\([^)]*\)", "", lowered)
    if parse_time_seconds(text) is not None:
        return "finished"
    return STATUS_ALIASES.get(lowered.rstrip("."), STATUS_ALIASES.get(lowered, "unknown"))


def normalize_name(value: Any) -> str | None:
    text = clean_text(value)
    if not text:
        return None
    if "," not in text:
        return text
    last, first = [part.strip() for part in text.split(",", 1)]
    return clean_text(f"{first} {last}")


def finalize_frame(rows: list[dict[str, Any]]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    for column in RESULT_COLUMNS:
        if column not in df.columns:
            df[column] = None
    if df.empty:
        return df[RESULT_COLUMNS]

    df["event"] = df["event"].map(normalize_event)
    df["athlete_name"] = df["athlete_name"].map(normalize_name)
    df["bib_number"] = df["bib_number"].map(parse_int).astype("Int64")
    df["year_of_birth"] = df["year_of_birth"].map(parse_int).astype("Int64")
    df["rank_within_heat"] = df["rank_within_heat"].map(parse_int).astype("Int64")
    df["heat"] = df["heat"].map(parse_int).astype("Int64")
    df["result_raw"] = df["result_raw"].map(clean_text)
    df["status"] = df["result_raw"].map(normalize_status)
    df["time_seconds"] = df["result_raw"].map(parse_time_seconds)
    for column in ["nationality", "club", "source_file", "source_type"]:
        df[column] = df[column].map(clean_text)
    df["gender"] = df["gender"].map(parse_gender)
    return df[RESULT_COLUMNS]

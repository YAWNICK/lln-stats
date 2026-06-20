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

TARGET_EVENTS = {
    "800m",
    "1500m",
    "5000m",
    "3000m Hindernis",
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


def normalize_event_feature(value: Any) -> str | None:
    raw_event = normalize_event(value)
    if raw_event in {"800m", "1500m", "5000m"}:
        return raw_event
    if raw_event and raw_event.startswith("3000m Hindernis"):
        return "3000m Hindernis"
    return None


def parse_gender(value: Any) -> str | None:
    text = clean_text(value)
    if not text:
        return None
    lower = text.lower()
    if "gemischt" in lower or re.search(r"\bm(?:ä|ae)nner\s*(?:&|und)\s*frauen\b", lower):
        return None
    gender_text = text.split(",", 1)[1] if "," in text else text
    lower = gender_text.lower()
    has_women = re.search(r"\b(w|weiblich(?:e|er)?|frauen|wju|w\d|kinder w|jugend w)\b", lower)
    has_men = re.search(r"\b(m|männlich(?:e|er)?|maennlich(?:e|er)?|männer|maenner|mju|m\d|kinder m|jugend m)\b", lower)
    if has_women:
        return "W"
    if has_men:
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
    if "raw_event" not in df.columns and "event" in df.columns:
        df["raw_event"] = df["event"]
    for column in RESULT_COLUMNS:
        if column not in df.columns:
            df[column] = None
    if df.empty:
        return df[RESULT_COLUMNS]

    df["raw_event"] = df["raw_event"].map(normalize_event)
    df["event"] = df["raw_event"].map(normalize_event_feature)
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


def renumber_gender_heats(df: pd.DataFrame) -> pd.DataFrame:
    """Turn gender-scoped source heat IDs into event-wide heat IDs.

    Event/gender sections retain their source order. Within each section, heat
    IDs retain their source order, so mixed-gender IDs cannot collide.
    """
    if df.empty:
        return df
    result = df.copy()
    for event in result["event"].dropna().unique():
        event_rows = result[result["event"] == event]
        groups = event_rows[["gender", "heat"]].drop_duplicates()
        groups = groups[groups["heat"].notna()]
        next_heat = 1
        for gender in groups["gender"].drop_duplicates().tolist():
            if pd.isna(gender):
                gender_rows = groups[groups["gender"].isna()]
                mask_gender = result["gender"].isna()
            else:
                gender_rows = groups[groups["gender"] == gender]
                mask_gender = result["gender"] == gender
            for old_heat in sorted(gender_rows["heat"].astype(int).unique()):
                mask = (result["event"] == event) & mask_gender & (result["heat"] == old_heat)
                result.loc[mask, "heat"] = next_heat
                next_heat += 1
    result["heat"] = result["heat"].astype("Int64")
    return result


def assign_heat_ranks(df: pd.DataFrame) -> pd.DataFrame:
    """Derive ordinal finish positions from times within each physical heat."""
    if df.empty:
        return df
    result = df.copy()
    result["rank_within_heat"] = pd.Series(pd.NA, index=result.index, dtype="Int64")
    finished = result["time_seconds"].notna() & result["heat"].notna()
    result.loc[finished, "rank_within_heat"] = (
        result.loc[finished]
        .groupby(["event", "heat"], dropna=False)["time_seconds"]
        .rank(method="first")
        .astype("Int64")
    )
    return result


def make_heat_ranks_unique(df: pd.DataFrame) -> pd.DataFrame:
    """Resolve tied source places with the next unused ordinal position."""
    if df.empty:
        return df
    result = df.copy()
    for _, heat_rows in result.groupby(["event", "heat"], dropna=False, sort=False):
        used: set[int] = set()
        for index, rank in heat_rows["rank_within_heat"].items():
            if pd.isna(rank):
                continue
            unique_rank = int(rank)
            while unique_rank in used:
                unique_rank += 1
            result.at[index, "rank_within_heat"] = unique_rank
            used.add(unique_rank)
    result["rank_within_heat"] = result["rank_within_heat"].astype("Int64")
    return result


def filter_target_results(df: pd.DataFrame) -> pd.DataFrame:
    """Keep only target LLN running events, excluding side events and relays."""
    if df.empty:
        return df
    relay_row = (
        df["athlete_name"].str.contains(r"\b(?:staffel|relay)\b", case=False, regex=True, na=False)
        | df["club"].str.contains(r"\b(?:staffel|relay)\b", case=False, regex=True, na=False)
    )
    filtered = df[df["event"].isin(TARGET_EVENTS) & ~relay_row].copy()
    return filtered[RESULT_COLUMNS].reset_index(drop=True)

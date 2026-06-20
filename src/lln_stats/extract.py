"""Public extraction API."""

from __future__ import annotations

from importlib import import_module
from pathlib import Path

import pandas as pd

from lln_stats.normalize import filter_target_results, make_heat_ranks_unique
from lln_stats.schema import RESULT_COLUMNS
from lln_stats.years import YEAR_SOURCES


def extract_year(year: int, root: str | Path = ".", target_only: bool = True) -> pd.DataFrame:
    source = YEAR_SOURCES[year]
    extractor = import_module(f"lln_stats.extractors.{source.extractor}")
    path = Path(root) / source.path
    df = extractor.extract(path)
    result = filter_target_results(df) if target_only else df
    result = make_heat_ranks_unique(result)
    _validate_unique_heat_ranks(result)
    return result


def extract_all(root: str | Path = ".", target_only: bool = True) -> pd.DataFrame:
    frames = [extract_year(year, root=root, target_only=target_only) for year in sorted(YEAR_SOURCES)]
    if not frames:
        return pd.DataFrame(columns=RESULT_COLUMNS)
    return pd.concat(frames, ignore_index=True)[RESULT_COLUMNS]


def _validate_unique_heat_ranks(df: pd.DataFrame) -> None:
    """Reject duplicate places within a physical event heat."""
    key = ["event_year", "event", "rank_within_heat", "heat"]
    ranked = df[
        df["event"].notna() & df["rank_within_heat"].notna() & df["heat"].notna()
    ]
    duplicates = ranked.duplicated(key, keep=False)
    if duplicates.any():
        sample = ranked.loc[duplicates, key + ["athlete_name"]].head(10)
        raise ValueError(f"Duplicate event heat ranks:\n{sample.to_string(index=False)}")

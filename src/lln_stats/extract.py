"""Public extraction API."""

from __future__ import annotations

from importlib import import_module
from pathlib import Path

import pandas as pd

from lln_stats.normalize import filter_target_results
from lln_stats.schema import RESULT_COLUMNS
from lln_stats.years import YEAR_SOURCES


def extract_year(year: int, root: str | Path = ".", target_only: bool = True) -> pd.DataFrame:
    source = YEAR_SOURCES[year]
    extractor = import_module(f"lln_stats.extractors.{source.extractor}")
    path = Path(root) / source.path
    df = extractor.extract(path)
    return filter_target_results(df) if target_only else df


def extract_all(root: str | Path = ".", target_only: bool = True) -> pd.DataFrame:
    frames = [extract_year(year, root=root, target_only=target_only) for year in sorted(YEAR_SOURCES)]
    if not frames:
        return pd.DataFrame(columns=RESULT_COLUMNS)
    return pd.concat(frames, ignore_index=True)[RESULT_COLUMNS]

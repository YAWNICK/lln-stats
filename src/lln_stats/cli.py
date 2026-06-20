"""Command line entry point for result extraction."""

from __future__ import annotations

import argparse
from pathlib import Path

from lln_stats.extract import extract_all, extract_year


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract Lange Laufnacht results.")
    parser.add_argument("--year", type=int, help="Extract one event year instead of all years.")
    parser.add_argument("--output", type=Path, help="Optional CSV or Parquet output path.")
    parser.add_argument(
        "--all-events",
        action="store_true",
        help="Include non-target events and younger age groups.",
    )
    args = parser.parse_args()

    target_only = not args.all_events
    df = extract_year(args.year, target_only=target_only) if args.year else extract_all(target_only=target_only)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        if args.output.suffix == ".parquet":
            df.to_parquet(args.output, index=False)
        else:
            df.to_csv(args.output, index=False)
        return
    print(df.to_string())


if __name__ == "__main__":
    main()

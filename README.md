# Lange Laufnacht Stats

This repository contains result data from the [Lange Laufnacht](https://lange-laufnacht.de) track and field meeting.

For a quick download, use one of these ready-made data files:

- [CSV export](features/results.csv) - opens in Excel, LibreOffice, Numbers, Google Sheets, and most other spreadsheet tools.
- [Parquet export](features/results.parquet) - a compact format for Python, R, DuckDB, and other data analysis tools.

The exported dataset currently contains 6,783 rows from event years 2016-2019 and 2021-2026. Lange Laufnacht did not take place in 2020 due to Covid.

## Data Columns

The exported files contain the same columns:

- `event_year`: year of the meeting
- `raw_event`: original event label from the source file
- `event`: normalized event name
- `athlete_name`: athlete name
- `bib_number`: bib number where available
- `gender`: athlete gender where available
- `year_of_birth`: athlete year of birth where available
- `nationality`: athlete nationality where available
- `club`: club or team where available
- `result_raw`: original result text from the source file
- `status`: normalized result status
- `time_seconds`: result converted to seconds where available
- `rank_within_heat`: rank within the heat where available
- `heat`: heat number or label where available
- `source_file`: source file used for the row
- `source_type`: extractor/source format used for the row

## Rebuilding The Exports

After changing source data or extractor code, rebuild the downloadable files from the repository root:

```bash
.venv/bin/lln-extract --output features/results.csv
.venv/bin/lln-extract --output features/results.parquet
```

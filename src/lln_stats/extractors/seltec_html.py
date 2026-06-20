"""Extractor for legacy SELTEC HTML result pages used from 2016 to 2018."""

from __future__ import annotations

import re
from pathlib import Path

from bs4 import BeautifulSoup, Tag

from lln_stats.normalize import finalize_frame, parse_gender, parse_result_mark


def extract(path: str | Path) -> object:
    source = Path(path)
    soup = BeautifulSoup(source.read_text(encoding="utf-8", errors="ignore"), "html.parser")
    event_year = int(source.parent.name)

    rows: list[dict[str, object]] = []
    current_event: str | None = None
    current_gender: str | None = None

    for node in soup.body.find_all(["p", "tr"], recursive=True):
        if isinstance(node, Tag) and node.name == "p" and "ev1" in (node.get("class") or []):
            current_event = node.get_text(" ", strip=True)
            if not re.search(r"\d+\s*m|\d+m|Hindernis", current_event):
                current_event = None
                current_gender = None
                continue
            current_gender = parse_gender(current_event)
            continue
        if not current_event or not isinstance(node, Tag) or node.name != "tr":
            continue

        cells = _cells_by_base_class(node)
        if "Name" not in cells or "Perf" not in cells:
            continue

        rank_from_mark, heat_from_mark = parse_result_mark(cells.get("Mark"))
        rows.append(
            {
                "event_year": event_year,
                "event": current_event,
                "athlete_name": cells.get("Name"),
                "bib_number": cells.get("BIB") or cells.get("Bib"),
                "gender": current_gender,
                "year_of_birth": cells.get("YOB"),
                "nationality": cells.get("Nat"),
                "club": cells.get("Team"),
                "result_raw": cells.get("Perf"),
                "rank_within_heat": rank_from_mark or cells.get("Pos"),
                "heat": heat_from_mark,
                "source_file": str(source),
                "source_type": "seltec_html",
            }
        )

    return finalize_frame(rows)


def _cells_by_base_class(row: Tag) -> dict[str, str]:
    cells: dict[str, str] = {}
    for cell in row.find_all("td", recursive=False):
        classes = cell.get("class") or []
        if not classes:
            continue
        match = re.match(r"hd([A-Za-z]+)", classes[0])
        if not match:
            continue
        base = re.sub(r"2$", "", match.group(1))
        cells[base] = cell.get_text(" ", strip=True)
    return cells

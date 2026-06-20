"""Extractor for legacy SELTEC HTML result pages used from 2016 to 2018."""

from __future__ import annotations

import re
from pathlib import Path

from bs4 import BeautifulSoup, Tag

from lln_stats.normalize import finalize_frame, normalize_event, parse_gender, parse_result_mark


def extract(path: str | Path) -> object:
    source = Path(path)
    soup = BeautifulSoup(source.read_text(encoding="utf-8", errors="ignore"), "html.parser")
    event_year = int(source.parent.name)

    rows: list[dict[str, object]] = []
    section_heats = _section_heats(soup)
    current_event: str | None = None
    current_gender: str | None = None
    current_table_gender: str | None = None
    current_heat: int | None = None

    for node in soup.body.find_all(["p", "tr"], recursive=True):
        if isinstance(node, Tag) and node.name == "p" and "ev1" in (node.get("class") or []):
            current_event = _section_title(node)
            if not _is_track_event(current_event) or _is_excluded_event(current_event):
                current_event = None
                current_gender = None
                current_table_gender = None
                current_heat = None
                continue
            current_gender = parse_gender(current_event)
            current_table_gender = current_gender
            current_heat = section_heats.get(id(node))
            continue
        if not current_event or not isinstance(node, Tag) or node.name != "tr":
            continue

        table_gender = _table_header_gender(node)
        if table_gender is not None:
            current_table_gender = table_gender
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
                "gender": current_table_gender or current_gender,
                "year_of_birth": cells.get("YOB"),
                "nationality": _nationality(cells.get("Nat"), event_year),
                "club": cells.get("Team"),
                "result_raw": cells.get("Perf"),
                "rank_within_heat": rank_from_mark or cells.get("Pos"),
                "heat": current_heat or heat_from_mark,
                "source_file": str(source),
                "source_type": "seltec_html",
            }
        )

    return finalize_frame(rows)


def _section_heats(soup: BeautifulSoup) -> dict[int, int]:
    sections: list[tuple[int, str, str | None, int | None, int]] = []
    for order, node in enumerate(soup.select("p.ev1")):
        title = _section_title(node)
        if not _is_track_event(title) or _is_excluded_event(title):
            continue
        event = normalize_event(title)
        if not event:
            continue
        sections.append((id(node), event, parse_gender(title), _section_start_minutes(node), order))

    heats: dict[int, int] = {}
    keys = {(event, gender) for _, event, gender, _, _ in sections}
    for key in keys:
        matching = [section for section in sections if (section[1], section[2]) == key]
        matching.sort(key=lambda section: (section[3] is None, section[3] or section[4], section[4]))
        for heat, section in enumerate(matching, start=1):
            heats[section[0]] = heat
    return heats


def _section_title(node: Tag) -> str:
    return node.get_text(" ", strip=True).split(" Datum:", 1)[0]


def _section_start_minutes(node: Tag) -> int | None:
    match = re.search(r"Beginn:\s*(\d{1,2}):(\d{2})", node.get_text(" ", strip=True))
    if not match:
        return None
    return int(match.group(1)) * 60 + int(match.group(2))


def _is_track_event(text: str | None) -> bool:
    return bool(text and re.search(r"\d+\s*m|\d+m|Hindernis", text))


def _is_excluded_event(text: str | None) -> bool:
    return bool(text and re.search(r"\bSchulstaffel\b", text, flags=re.IGNORECASE))


def _nationality(value: str | None, event_year: int) -> str | None:
    if event_year in {2016, 2017, 2018} and not value:
        return "GER"
    return value


def _table_header_gender(row: Tag) -> str | None:
    for cell in row.find_all("td", recursive=False):
        classes = cell.get("class") or []
        if classes and classes[0] == "ht1":
            return parse_gender(cell.get_text(" ", strip=True))
    return None


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

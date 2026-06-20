"""Coordinate-based extractor for official result PDFs."""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pdfplumber

from lln_stats.normalize import finalize_frame, normalize_event, parse_gender, parse_result_mark


EVENT_RE = re.compile(r"(?<![A-Za-z])(?:\d[.\d]*\s*m|[1-9]\d{2,3}m)(?:\s+Hindernis)?")
RESULT_RE = re.compile(r"^(?:\d+(?::\d{1,2}){0,2},\d+|\d+(?::\d{1,2}){1,2}|aufg\.?|abg\.?|ab\.?|n\.a\.?|disq\.?)$")


@dataclass
class Line:
    words: list[dict[str, object]]

    @property
    def text(self) -> str:
        return " ".join(str(word["text"]) for word in self.words)

    def between(self, left: float, right: float) -> list[str]:
        return [str(word["text"]) for word in self.words if left <= float(word["x0"]) < right]


def extract(path: str | Path) -> object:
    source = Path(path)
    event_year = int(source.parent.name)
    rows: list[dict[str, object]] = []
    gender_lookup = _load_gender_lookup(source)
    current_event_line: str | None = None
    current_event: str | None = None
    current_gender: str | None = None
    current_heat: int | None = None
    inferred_heat_counts: dict[tuple[str | None, str | None], int] = {}
    last_row: dict[str, object] | None = None

    with pdfplumber.open(source) as pdf:
        for page in pdf.pages:
            for line in _iter_lines(page.extract_words(x_tolerance=1, y_tolerance=3)):
                text = line.text
                if _is_noise(text):
                    continue

                event_line = _event_line(text)
                if event_line:
                    current_event_line = event_line
                    current_event = normalize_event(event_line)
                    current_gender = parse_gender(event_line)
                    current_heat = (
                        _next_inferred_heat(inferred_heat_counts, current_event, current_gender)
                        if event_year == 2019
                        else None
                    )
                    last_row = None
                    continue

                heat = _heat_from_line(text)
                if heat is not None:
                    if event_year != 2019:
                        current_heat = heat
                    last_row = None
                    continue

                if not current_event:
                    continue

                row = _parse_result_line(line)
                if row:
                    rank_from_mark, heat_from_mark = parse_result_mark(row.pop("mark", None))
                    gender = current_gender or parse_gender(current_event_line)
                    if gender is None and event_year == 2019 and current_event == "5000m":
                        gender = gender_lookup.get(str(row.get("athlete_name") or ""))
                    row.update(
                        {
                            "event_year": event_year,
                            "event": current_event,
                            "gender": gender,
                            "rank_within_heat": rank_from_mark or row.get("rank"),
                            "heat": _row_heat(event_year, current_heat, heat_from_mark),
                            "source_file": str(source),
                            "source_type": "result_pdf",
                        }
                    )
                    row.pop("rank", None)
                    rows.append(row)
                    last_row = row
                    continue

                if last_row is not None and _looks_like_club_continuation(line):
                    extra = " ".join(line.between(270, 420))
                    if extra:
                        last_row["club"] = f"{last_row.get('club') or ''} {extra}".strip()

    return finalize_frame(rows)


def _load_gender_lookup(source: Path) -> dict[str, str]:
    path = source.parent / "5000m_mixed_gender_lookup.csv"
    if not path.exists():
        return {}
    with path.open(encoding="utf-8", newline="") as csv_file:
        return {
            row["athlete_name"]: row["gender"]
            for row in csv.DictReader(csv_file)
            if row.get("athlete_name") and row.get("gender")
        }


def _iter_lines(words: Iterable[dict[str, object]]) -> Iterable[Line]:
    lines: list[list[dict[str, object]]] = []
    for word in sorted(words, key=lambda w: (float(w["top"]), float(w["x0"]))):
        if not lines or abs(float(word["top"]) - float(lines[-1][0]["top"])) > 3:
            lines.append([word])
        else:
            lines[-1].append(word)
    for words_in_line in lines:
        yield Line(sorted(words_in_line, key=lambda w: float(w["x0"])))


def _is_noise(text: str) -> bool:
    return (
        not text
        or text.startswith("Dataservice by")
        or text.startswith("Gedruckt am")
        or text.startswith("Internet-Service:")
        or text.startswith("Seite ")
        or text.startswith("ERGEBNISSE")
        or text.startswith("Legende")
        or text.startswith("Ergebnis Offiziell")
        or text.startswith("Zwischenzeiten")
        or text in {"Rang StNr Name", "Jg Nat Verein Leistung", "Zeitläufe"}
    )


def _event_line(text: str) -> str | None:
    if text.startswith(("Rang ", "StNr ", "Jg ", "Nat ", "Verein ", "Leistung ")):
        return None
    if "Zwischenzeiten" in text or "Wind:" in text:
        return None
    if re.fullmatch(r"\d{3,4}m\s+\d+(?::\d{1,2})?,\d+", text):
        return None
    if re.fullmatch(r"\d{3,4}m", text.replace(" ", "")):
        return None
    if EVENT_RE.search(text) and not re.match(r"^\d+\s+\d+\s+", text):
        return text
    return None


def _heat_from_line(text: str) -> int | None:
    match = re.match(r"Zeitlauf\s+(\d+)", text)
    return int(match.group(1)) if match else None


def _next_inferred_heat(
    counts: dict[tuple[str | None, str | None], int],
    event: str | None,
    gender: str | None,
) -> int:
    key = (event, gender)
    counts[key] = counts.get(key, 0) + 1
    return counts[key]


def _row_heat(event_year: int, current_heat: int | None, heat_from_mark: int | None) -> int:
    if event_year == 2019:
        return current_heat or heat_from_mark or 1
    return heat_from_mark or current_heat or 1


def _parse_result_line(line: Line) -> dict[str, object] | None:
    bib = " ".join(line.between(58, 80))
    name = " ".join(line.between(80, 219))
    year = " ".join(line.between(219, 243))
    nationality = " ".join(line.between(243, 270))
    club = " ".join(line.between(270, 420))
    result = " ".join(line.between(420, 485))
    mark = " ".join(line.between(485, 570))
    rank = " ".join(line.between(30, 58))

    if not re.fullmatch(r"\d+", bib or ""):
        return None
    if not re.fullmatch(r"\d{4}", year or ""):
        return None
    if not name or not result or not RESULT_RE.match(result):
        return None

    return {
        "rank": rank,
        "athlete_name": name,
        "bib_number": bib,
        "year_of_birth": year,
        "nationality": nationality,
        "club": club,
        "result_raw": result,
        "mark": mark,
    }


def _looks_like_club_continuation(line: Line) -> bool:
    text = line.text
    if not text or re.match(r"^\d+\s+\d+\s+", text):
        return False
    if _is_noise(text) or _event_line(text) or _heat_from_line(text):
        return False
    return bool(line.between(270, 420)) and not line.between(58, 80)

"""Extractor for SELTEC XML result exports."""

from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree as ET

from lln_stats.normalize import finalize_frame, normalize_event_code


def extract(path: str | Path) -> object:
    source = Path(path)
    root = ET.parse(source).getroot()
    event_year = int(root.attrib["begindate"][:4])

    clubs = {
        club.attrib["id"]: club.attrib
        for club in root.findall(".//club")
        if "id" in club.attrib
    }
    athletes = {
        athlete.attrib["id"]: athlete.attrib
        for athlete in root.findall(".//athlete")
        if "id" in athlete.attrib
    }
    events = {
        event.attrib["id"]: normalize_event_code(event.attrib.get("code"))
        for event in root.findall(".//event")
        if "id" in event.attrib
    }

    rows: list[dict[str, object]] = []
    for round_node in root.findall(".//round"):
        round_id = round_node.attrib.get("roundid")
        if not round_id:
            continue
        event = events.get(round_node.attrib.get("event", ""))
        if not event:
            continue

        for result in round_node.findall("./results/individual"):
            athlete = athletes.get(result.attrib.get("athlete", ""))
            if not athlete:
                continue
            club = clubs.get(athlete.get("club", ""), {})
            place = result.attrib.get("place")
            rows.append(
                {
                    "event_year": event_year,
                    "event": event,
                    "athlete_name": f"{athlete.get('forename', '')} {athlete.get('lastname', '')}",
                    "bib_number": athlete.get("number"),
                    "gender": athlete.get("sex"),
                    "year_of_birth": athlete.get("yearofbirth"),
                    "nationality": athlete.get("country"),
                    "club": club.get("name"),
                    "result_raw": result.attrib.get("result"),
                    "rank_within_heat": place if place and place != "0" else None,
                    "heat": round_id,
                    "source_file": str(source),
                    "source_type": "seltec_xml",
                }
            )

    return finalize_frame(rows)

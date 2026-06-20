"""Explicit source selection by event year."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class YearSource:
    year: int
    path: Path
    extractor: str


YEAR_SOURCES = {
    2016: YearSource(
        2016,
        Path("data/2016/2016-05-20-Karlsruhe-Ergebnisse-Lange-Laufnacht.htm"),
        "seltec_html",
    ),
    2017: YearSource(
        2017,
        Path("data/2017/2017-05-19-Karlsruhe-Ergebnisliste.htm"),
        "seltec_html",
    ),
    2018: YearSource(
        2018,
        Path("data/2018/2018-05-19-Karlsruhe-Ergebnisliste.htm"),
        "seltec_html",
    ),
    2019: YearSource(
        2019,
        Path("data/2019/2019-05-18-Karlsruhe-Ergebnisse.pdf"),
        "result_pdf",
    ),
    2021: YearSource(
        2021,
        Path("data/2021/5. Lange Laufnacht _results.xml"),
        "seltec_xml",
    ),
    2022: YearSource(
        2022,
        Path("data/2022/6. Lange Laufnacht_results.xml"),
        "seltec_xml",
    ),
    2023: YearSource(
        2023,
        Path("data/2023/2023-05-20-Karlsruhe-Ergebnisliste.pdf"),
        "result_pdf",
    ),
    2024: YearSource(
        2024,
        Path("data/2024/2024-05-11-Karlsruhe-Ergebnisliste.pdf"),
        "result_pdf",
    ),
    2025: YearSource(
        2025,
        Path("data/2025/2025-05-31-Karlsruhe-Ergebnisliste.pdf"),
        "result_pdf",
    ),
    2026: YearSource(
        2026,
        Path("data/2026/2026-05-30-Karlsruhe-Ergebnisliste-corrected.pdf"),
        "result_pdf",
    ),
}

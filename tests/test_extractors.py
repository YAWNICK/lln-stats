from lln_stats.extract import extract_year
from lln_stats.normalize import parse_result_mark, parse_time_seconds
from lln_stats.schema import RESULT_COLUMNS


def test_normalize_time_and_mark() -> None:
    assert parse_time_seconds("1:47,42") == 107.42
    assert parse_time_seconds("14:01,23") == 841.23
    assert parse_time_seconds("aufg.") is None
    assert parse_result_mark("2./XI") == (2, 11)
    assert parse_result_mark("-/XIII") == (None, 13)


def test_legacy_html_2016_row() -> None:
    df = extract_year(2016)
    assert list(df.columns) == RESULT_COLUMNS
    row = df.iloc[0]
    assert row.event_year == 2016
    assert row.event == "800m"
    assert row.athlete_name == "Ludolph Sören"
    assert row.bib_number == 15
    assert row.gender == "M"
    assert row.year_of_birth == 1988
    assert row.result_raw == "1:47,42"
    assert row.rank_within_heat == 1
    assert row.heat == 1


def test_pdf_2019_uses_heat_sections() -> None:
    df = extract_year(2019)
    row = df.iloc[0]
    assert row.event == "800m"
    assert row.athlete_name == "Hartmann Rolf"
    assert row.bib_number == 130
    assert row.nationality == "GER"
    assert row.result_raw == "2:06,97"
    assert row.rank_within_heat == 1
    assert row.heat == 1


def test_xml_2021_uses_bib_country_and_heat_round() -> None:
    df = extract_year(2021)
    row = df.iloc[0]
    assert row.event == "1500m"
    assert row.athlete_name == "Ismael Debjani"
    assert row.bib_number == 55
    assert row.gender == "M"
    assert row.nationality == "BEL"
    assert row.rank_within_heat == 1
    assert row.heat == 3


def test_pdf_2023_uses_rank_heat_mark() -> None:
    df = extract_year(2023)
    row = df.iloc[0]
    assert row.event == "800m"
    assert row.athlete_name == "Ostrowski Filip"
    assert row.bib_number == 762
    assert row.nationality == "POL"
    assert row.result_raw == "1:45,62"
    assert row.rank_within_heat == 1
    assert row.heat == 11


def test_pdf_2024_does_not_treat_wind_as_event() -> None:
    df = extract_year(2024)
    row = df.iloc[0]
    assert row.event == "100m"
    assert row.athlete_name == "Burraj Franko"
    assert row.result_raw == "10,63"

from lln_stats.extract import extract_year
from lln_stats.normalize import TARGET_EVENTS, parse_gender, parse_result_mark, parse_time_seconds
from lln_stats.schema import RESULT_COLUMNS


def test_normalize_time_and_mark() -> None:
    assert parse_time_seconds("1:47,42") == 107.42
    assert parse_time_seconds("14:01,23") == 841.23
    assert parse_time_seconds("aufg.") is None
    assert parse_result_mark("2./XI") == (2, 11)
    assert parse_result_mark("-/XIII") == (None, 13)
    assert parse_gender("M&M Sports 800m, Weiblich - Zeitläufe") == "W"
    assert parse_gender("800m M&M Sports, W, WJU20, WJU18 18.05.2019 / 17:58") == "W"
    assert parse_gender("5000m Fiducia & GAD, Männer & Frauen 18.05.2019 / 16:15") is None


def test_legacy_html_2016_row() -> None:
    df = extract_year(2016)
    assert list(df.columns) == RESULT_COLUMNS
    row = df.iloc[0]
    assert row.event_year == 2016
    assert row.raw_event == "800m"
    assert row.event == "800m"
    assert row.athlete_name == "Ludolph Sören"
    assert row.bib_number == 15
    assert row.gender == "M"
    assert row.year_of_birth == 1988
    assert row.result_raw == "1:47,42"
    assert row.rank_within_heat == 1
    assert row.heat == 7


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
    later_heat = df[df.athlete_name == "Belbachir Mohamed"].iloc[0]
    assert later_heat.result_raw == "1:46,00"
    assert later_heat.heat == 11


def test_mixed_sections_get_row_gender() -> None:
    df_2016 = extract_year(2016)
    assert df_2016[df_2016.athlete_name == "Sujew Elina"].iloc[0].gender == "W"
    assert df_2016[df_2016.athlete_name == "Rauscher Silvan"].iloc[0].gender == "M"

    df_2019 = extract_year(2019)
    assert df_2019[df_2019.athlete_name == "Hettinger Henrik"].iloc[0].gender == "M"
    assert df_2019[df_2019.athlete_name == "Weishäuptl Miriam"].iloc[0].gender == "W"
    assert df_2019.gender.isna().sum() == 0


def test_legacy_html_defaults_empty_nationality_to_germany() -> None:
    for year in [2016, 2017, 2018]:
        df = extract_year(year)
        assert df.nationality.isna().sum() == 0
        assert (df.nationality.str.strip() == "").sum() == 0


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
    df = extract_year(2024, target_only=False)
    row = df.iloc[0]
    assert row.raw_event == "100m"
    assert df.event.isna().iloc[0]
    assert row.athlete_name == "Burraj Franko"
    assert row.result_raw == "10,63"


def test_default_extraction_keeps_target_events_and_skips_side_events() -> None:
    df = extract_year(2024)
    assert set(df.event.dropna().unique()) <= TARGET_EVENTS
    assert df.event.isna().sum() == 0
    assert "100m" not in set(df.event.dropna())
    assert "1000m" not in set(df.event.dropna())


def test_event_collapses_steeplechase_heights() -> None:
    df = extract_year(2023)
    steeplechase = df[df.raw_event.str.contains("Hindernis", na=False)]
    assert set(steeplechase.raw_event.unique()) == {
        "3000m Hindernis",
        "3000m Hindernis 0.762m",
        "3000m Hindernis 0.914m",
    }
    assert set(steeplechase.event.unique()) == {"3000m Hindernis"}


def test_default_extraction_keeps_younger_athletes_in_u18_races() -> None:
    df = extract_year(2021)
    row = df[df.athlete_name == "Yannick Graf"].iloc[0]
    assert row.event == "800m"
    assert row.year_of_birth == 2006


def test_default_extraction_skips_flat_3000m_and_relay_rows() -> None:
    df_2017 = extract_year(2017)
    assert "3000m" not in set(df_2017.event.dropna())
    assert not df_2017.athlete_name.str.contains("Staffel", case=False, na=False).any()

"""Tests for the pure pipeline logic.

Deliberately no network and no database — these cover the parts that decide what
the reader sees, and that have already produced real bugs: substring matching,
and merging stories that only look alike.
"""

from __future__ import annotations

import pytest

from nyhetsradar.app import short_date, week_window
from nyhetsradar.collect import _PAYWALL_PREFIX, clean
from nyhetsradar.dedup import normalise, similar
from nyhetsradar.score import find_terms, gate_and_score

# ── keyword matching ─────────────────────────────────────────────────────────


def test_word_boundaries_reject_substrings():
    """The bug that shipped first: 'Ski' matched inside 'skisse'."""
    assert find_terms("nye skisser for skillevegg", ["ski"]) == []
    assert find_terms("boliger i ski sentrum", ["ski"]) == ["ski"]


def test_loren_does_not_match_lorenskog():
    assert find_terms("blokker i lørenskog", ["løren"]) == []
    assert find_terms("blokker i lørenskog", ["lørenskog"]) == ["lørenskog"]


def test_multiword_terms_tolerate_extra_whitespace():
    assert find_terms("selvaag  bolig leverer", ["selvaag bolig"]) == ["selvaag bolig"]


def test_matching_is_case_insensitive():
    assert find_terms("Selvaag Eiendom kjøper", ["selvaag eiendom"]) == ["selvaag eiendom"]


# ── the gate ─────────────────────────────────────────────────────────────────


def row(title: str, snippet: str = "") -> dict:
    return {
        "title": title,
        "snippet": snippet,
        "published_at": None,
        "collected_at": "2026-09-03T06:00:00+00:00",
    }


VOCAB = {
    "entities": {"own": ["selvaag"], "competitors": ["obos"], "places": ["oslo"]},
    "themes": ["boligmarkedet"],
}


def test_gate_blocks_items_matching_nothing():
    result = gate_and_score(row("Ny kokebok fra kjendiskokken"), VOCAB, 1)
    assert result["gated"] == 0
    assert result["score"] is None


def test_gate_passes_on_a_single_theme_hit():
    result = gate_and_score(row("Boligmarkedet flater ut"), VOCAB, 1)
    assert result["gated"] == 1
    assert result["theme_hits"] == "boligmarkedet"


def test_own_company_outscores_a_bare_theme():
    own = gate_and_score(row("Selvaag kjøper tomt"), VOCAB, 1)
    theme = gate_and_score(row("Boligmarkedet flater ut"), VOCAB, 1)
    assert own["score"] > theme["score"]


def test_score_stays_within_bounds():
    loud = row("Selvaag og Obos i Oslo om boligmarkedet", "Selvaag Obos Oslo boligmarkedet")
    result = gate_and_score(loud, VOCAB, 40)
    assert 0 <= result["score"] <= 100


def test_more_sources_raises_the_score():
    one = gate_and_score(row("Selvaag kjøper tomt"), VOCAB, 1)
    many = gate_and_score(row("Selvaag kjøper tomt"), VOCAB, 6)
    assert many["score"] > one["score"]


# ── deduplication ────────────────────────────────────────────────────────────


def test_same_story_from_two_outlets_merges():
    a = normalise("Ny leder for Peab Eiendomsutvikling Norge")
    b = normalise("Hun blir ny sjef i Peab Eiendomsutvikling Norge")
    assert similar(a, b) >= 0.82


def test_same_shape_different_month_does_not_merge():
    """The false merge that lowering the threshold would have caused."""
    a = normalise("Boligprisene steg 0,5 prosent i februar")
    b = normalise("Boligprisene falt 2,6 prosent i juli")
    assert similar(a, b) < 0.82


def test_normalise_strips_stopwords_and_punctuation():
    assert "og" not in normalise("Selvaag og Backe i Oslo!").split()


def test_reordered_headline_still_matches():
    """The same deal told from either side is one story."""
    a = normalise("Skanska kjøper Skøyen-tomt fra Selvaag")
    b = normalise("Selvaag selger Skøyen-tomt til Skanska")
    assert similar(a, b) >= 0.82


def test_differing_figures_veto_a_merge():
    """Market headlines are identical in shape and differ only in the number."""
    a = normalise("Obos-prisene i Oslo falt med 0,3 prosent")
    b = normalise("Obos-prisene i Oslo falt 2 prosent i september")
    assert similar(a, b) == 0.0


def test_quarterly_results_stay_separate():
    a = normalise("Selvaag Bolig ASA: Q1 2026: Rekordsalg")
    b = normalise("Selvaag Bolig ASA: Q2 2026: Rekordsalg og god lønnsomhet")
    assert similar(a, b) < 0.82


def test_a_figure_in_only_one_headline_does_not_veto():
    """One outlet putting the price in the headline is still the same story."""
    a = normalise("Peab kjøper Huseby-tomten i Oslo")
    b = normalise("Peab kjøper Huseby-tomten i Oslo for 200 millioner")
    assert similar(a, b) >= 0.82


def test_generic_shared_words_do_not_merge_unrelated_trade_stories():
    """Containment alone merged these two; the overlap floor separates them."""
    a = normalise("Her er de største rådgiverne i bygg og anlegg")
    b = normalise("Konkursnedgang, men seks av de ti største kom i bygg og anlegg")
    assert similar(a, b) < 0.82


# ── collection hygiene ───────────────────────────────────────────────────────


@pytest.mark.parametrize("raw", ["(+) Selvaag i Bergen", "+ Selvaag i Bergen"])
def test_paywall_prefix_is_stripped(raw):
    assert _PAYWALL_PREFIX.sub("", raw).strip() == "Selvaag i Bergen"


def test_clean_strips_markup_and_collapses_whitespace():
    assert clean("<p>Hei   <b>der</b></p>") == "Hei der"


def test_clean_truncates_to_a_snippet():
    assert len(clean("x" * 900)) == 400


# ── Norwegian formatting ─────────────────────────────────────────────────────


def test_short_date_is_norwegian_and_unpadded():
    assert short_date("2026-09-02T10:00:00+00:00") == "2. sep"


def test_short_date_tolerates_missing_and_malformed_values():
    assert short_date(None) == ""
    assert short_date("not a date") == ""


def test_week_window_spans_monday_to_sunday():
    from datetime import UTC, datetime

    week = week_window(datetime(2026, 9, 3, tzinfo=UTC))  # a Thursday
    assert week["number"] == 36
    assert week["start"].weekday() == 0
    assert "31. august" in week["range"]

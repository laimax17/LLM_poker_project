"""Tests for living-opponents: banter lines + tilt modifier."""
from backend.src.ai.banter import get_banter
from backend.src.ai.gto_strategy import GTOBotStrategy


def test_banter_returns_line_for_known_event():
    line = get_banter('won_big', 'maniac', 'en')
    assert isinstance(line, str) and len(line) > 0


def test_banter_falls_back_to_generic_personality():
    # 'won_big' has no 'tag'-specific 'doubled_up'; generic pool covers it.
    line = get_banter('doubled_up', 'tag', 'en')
    assert isinstance(line, str) and len(line) > 0


def test_banter_locale_fallback_to_english():
    # Unknown locale falls back to English pool.
    line = get_banter('eliminated', 'rock', 'fr')
    assert isinstance(line, str) and len(line) > 0


def test_banter_unknown_event_returns_none():
    assert get_banter('no_such_event', 'shark', 'en') is None


def test_tilt_widens_modifiers():
    s = GTOBotStrategy('rock')
    base = s._mods
    s.tilt = 1.0
    tilted = s._mods
    assert tilted.open_freq_mult > base.open_freq_mult   # plays more hands
    assert tilted.bluff_freq_mult > base.bluff_freq_mult  # bluffs more
    assert tilted.call_margin_offset < base.call_margin_offset  # calls lighter


def test_zero_tilt_is_identity():
    s = GTOBotStrategy('shark')
    s.tilt = 0.0
    assert s._mods is s._base_mods

"""Tests for all-in showdown equity (src/ai/showdown.py)."""
from backend.src.engine import Card, Rank, Suit
from backend.src.ai.showdown import compute_allin_equities, equities_payload


def C(rank, suit):
    return Card(rank, suit)


def test_single_contestant_wins_all():
    eq = compute_allin_equities([('a', [C(Rank.ACE, Suit.SPADES), C(Rank.KING, Suit.SPADES)])], [])
    assert eq['a'] == 1.0


def test_aa_vs_kk_preflop():
    aa = [C(Rank.ACE, Suit.SPADES), C(Rank.ACE, Suit.HEARTS)]
    kk = [C(Rank.KING, Suit.SPADES), C(Rank.KING, Suit.HEARTS)]
    eq = compute_allin_equities([('a', aa), ('b', kk)], [], n_sim=4000)
    # AA is roughly 80-85% favourite
    assert 0.78 <= eq['a'] <= 0.88
    assert abs(eq['a'] + eq['b'] - 1.0) < 1e-6


def test_complete_board_is_deterministic():
    # Full 5-card board → exact result, no sampling.
    a = [C(Rank.ACE, Suit.SPADES), C(Rank.ACE, Suit.HEARTS)]
    b = [C(Rank.KING, Suit.SPADES), C(Rank.KING, Suit.HEARTS)]
    board = [
        C(Rank.ACE, Suit.CLUBS), C(Rank.QUEEN, Suit.DIAMONDS),
        C(Rank.SEVEN, Suit.HEARTS), C(Rank.THREE, Suit.SPADES),
        C(Rank.TWO, Suit.DIAMONDS),
    ]
    eq = compute_allin_equities([('a', a), ('b', b)], board)
    assert eq['a'] == 1.0  # trip aces beats pair of kings
    assert eq['b'] == 0.0


def test_split_pot_equity():
    # Both players play the board (royal-ish) → split.
    a = [C(Rank.TWO, Suit.SPADES), C(Rank.THREE, Suit.HEARTS)]
    b = [C(Rank.TWO, Suit.HEARTS), C(Rank.THREE, Suit.SPADES)]
    board = [
        C(Rank.ACE, Suit.CLUBS), C(Rank.KING, Suit.CLUBS),
        C(Rank.QUEEN, Suit.CLUBS), C(Rank.JACK, Suit.CLUBS),
        C(Rank.TEN, Suit.CLUBS),  # royal flush on board
    ]
    eq = compute_allin_equities([('a', a), ('b', b)], board)
    assert abs(eq['a'] - 0.5) < 1e-6
    assert abs(eq['b'] - 0.5) < 1e-6


def test_flop_enumeration_sums_to_one():
    a = [C(Rank.ACE, Suit.SPADES), C(Rank.KING, Suit.SPADES)]
    b = [C(Rank.QUEEN, Suit.HEARTS), C(Rank.QUEEN, Suit.DIAMONDS)]
    board = [C(Rank.ACE, Suit.HEARTS), C(Rank.SEVEN, Suit.CLUBS), C(Rank.TWO, Suit.DIAMONDS)]
    eq = compute_allin_equities([('a', a), ('b', b)], board)
    assert abs(sum(eq.values()) - 1.0) < 1e-6


def test_payload_shape():
    a = [C(Rank.ACE, Suit.SPADES), C(Rank.ACE, Suit.HEARTS)]
    b = [C(Rank.KING, Suit.SPADES), C(Rank.KING, Suit.HEARTS)]
    payload = equities_payload([('human', 'PLAYER', a), ('bot_1', 'NEON', b)], [])
    assert len(payload['board']) == 0
    assert len(payload['players']) == 2
    assert {p['id'] for p in payload['players']} == {'human', 'bot_1'}
    assert all(0.0 <= p['equity'] <= 1.0 for p in payload['players'])

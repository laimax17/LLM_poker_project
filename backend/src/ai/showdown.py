"""
All-in showdown equity.

When 2+ players are all-in, computes each contestant's chance of winning the
hand from the board state at the moment the action closed (before the engine
runs out the remaining community cards). This is the classic "65% vs 35%"
all-in equity shown on poker broadcasts.

Unlike ai/equity.py (which estimates vs *random* opponents), here every hole
card is known, so we evaluate the exact field by enumerating or sampling the
remaining board.
"""
from __future__ import annotations

import random
from itertools import combinations
from math import comb
from typing import Any

from ..engine import Card, HandEvaluator, Rank, Suit

# If the number of possible run-outs is at most this, enumerate exactly;
# otherwise Monte-Carlo sample.
ENUM_LIMIT = 2000
DEFAULT_SIMS = 400


def _full_deck() -> list[Card]:
    return [Card(r, s) for r in Rank for s in Suit]


def _hand_key(seven: list[Card]) -> tuple[int, tuple[int, ...]]:
    rank, tiebreakers = HandEvaluator.evaluate(seven)
    return (rank.value, tuple(tiebreakers))


def compute_allin_equities(
    contestants: list[tuple[str, list[Card]]],
    board: list[Card],
    n_sim: int = DEFAULT_SIMS,
) -> dict[str, float]:
    """Return {player_id: win_fraction} for an all-in confrontation.

    contestants: list of (player_id, two hole cards).
    board: community cards already dealt (0, 3, or 4 cards).
    Split pots award fractional wins.
    """
    ids = [pid for pid, _ in contestants]
    if len(contestants) < 2:
        return {pid: 1.0 for pid in ids}

    used = {(c.rank.value, c.suit.value) for _, cards in contestants for c in cards}
    used |= {(c.rank.value, c.suit.value) for c in board}
    deck = [c for c in _full_deck() if (c.rank.value, c.suit.value) not in used]

    need = 5 - len(board)
    wins: dict[str, float] = {pid: 0.0 for pid in ids}

    if need <= 0:
        runouts: list[tuple[Card, ...]] = [tuple()]
    elif comb(len(deck), need) <= ENUM_LIMIT:
        runouts = list(combinations(deck, need))
    else:
        runouts = [tuple(random.sample(deck, need)) for _ in range(n_sim)]

    for extra in runouts:
        full_board = board + list(extra)
        best_key = None
        winners: list[str] = []
        for pid, hole in contestants:
            key = _hand_key(hole + full_board)
            if best_key is None or key > best_key:
                best_key = key
                winners = [pid]
            elif key == best_key:
                winners.append(pid)
        share = 1.0 / len(winners)
        for w in winners:
            wins[w] += share

    total = len(runouts)
    return {pid: (wins[pid] / total if total else 0.0) for pid in ids}


def equities_payload(
    contestants: list[tuple[str, str, list[Card]]],
    board: list[Card],
) -> dict[str, Any]:
    """Build the socket payload. contestants: (id, name, hole cards)."""
    eq = compute_allin_equities([(pid, hole) for pid, _, hole in contestants], board)
    return {
        'board': [c.to_dict() for c in board],
        'players': [
            {'id': pid, 'name': name, 'equity': round(eq.get(pid, 0.0), 3)}
            for pid, name, _ in contestants
        ],
    }

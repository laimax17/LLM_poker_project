"""
Monte Carlo equity estimator for Texas Hold'em.

Estimates win probability via random simulation — no external poker library
required. Uses the project's existing HandEvaluator.
"""
from __future__ import annotations

import logging
import random
from typing import List

from ..engine import Card, HandEvaluator
from ..schemas import Rank, Suit

logger = logging.getLogger(__name__)

# ─── Full deck helper ─────────────────────────────────────────────────────────

def _build_full_deck() -> List[Card]:
    """Return a list of all 52 cards."""
    return [Card(rank=r, suit=s) for r in Rank for s in Suit]


def _card_key(card: Card) -> tuple[int, str]:
    return (card.rank.value, card.suit.value)


# ─── Main estimator ───────────────────────────────────────────────────────────

def estimate_equity(
    my_hand: List[Card],
    community: List[Card],
    num_opponents: int,
    n_sim: int = 400,
) -> float:
    """
    Estimate win equity via Monte Carlo simulation.

    Parameters
    ----------
    my_hand : list[Card]
        The 2 hole cards of the evaluating player.
    community : list[Card]
        Currently visible community cards (0–5).
    num_opponents : int
        Number of active opponents still in the hand.
    n_sim : int
        Number of simulations. 400 ≈ 3–6ms on typical hardware.

    Returns
    -------
    float
        Estimated equity in [0.0, 1.0].
        Formula: (wins + 0.5 * ties) / n_sim
    """
    if not my_hand or num_opponents <= 0:
        return 0.5

    num_opponents = max(1, min(num_opponents, 5))
    cards_needed = 5 - len(community)  # community cards still to come

    # Build the remaining deck (exclude known cards)
    known_keys = {_card_key(c) for c in my_hand + community}
    remaining = [c for c in _build_full_deck() if _card_key(c) not in known_keys]

    wins = 0
    ties = 0

    for _ in range(n_sim):
        try:
            # Sample enough cards for opponents + remaining board
            cards_needed_total = num_opponents * 2 + cards_needed
            if cards_needed_total > len(remaining):
                # Edge case: not enough cards (should never happen in valid state)
                break

            sampled = random.sample(remaining, cards_needed_total)

            # Distribute: first (num_opponents * 2) cards go to opponents
            opp_hands: List[List[Card]] = []
            for i in range(num_opponents):
                opp_hands.append([sampled[i * 2], sampled[i * 2 + 1]])

            # Remaining cards complete the board
            board = list(community) + sampled[num_opponents * 2:]

            # Evaluate all hands (need exactly 5-card board)
            my_rank, my_tb = HandEvaluator.evaluate(my_hand + board)

            best_opp_rank = None
            best_opp_tb: List[int] = []
            for opp_hand in opp_hands:
                opp_rank, opp_tb = HandEvaluator.evaluate(opp_hand + board)
                if best_opp_rank is None or opp_rank.value > best_opp_rank.value:
                    best_opp_rank = opp_rank
                    best_opp_tb = opp_tb
                elif opp_rank.value == best_opp_rank.value and opp_tb > best_opp_tb:
                    best_opp_tb = opp_tb

            if best_opp_rank is None:
                wins += 1
                continue

            if my_rank.value > best_opp_rank.value:
                wins += 1
            elif my_rank.value == best_opp_rank.value:
                if my_tb > best_opp_tb:
                    wins += 1
                elif my_tb == best_opp_tb:
                    ties += 1
                # else: loss
        except Exception as exc:
            logger.debug('equity sim error: %s', exc)
            continue

    total = n_sim
    if total == 0:
        return 0.5
    return (wins + 0.5 * ties) / total

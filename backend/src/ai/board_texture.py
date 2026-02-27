"""
Board texture analyzer for Texas Hold'em community cards.

Classifies the board as dry / semi-wet / wet and detects draws.
Used by GTO strategy and GTO coach to select appropriate bet sizing.
"""
from __future__ import annotations

import logging
from collections import Counter
from dataclasses import dataclass
from typing import List

from ..engine import Card

logger = logging.getLogger(__name__)


@dataclass
class BoardTexture:
    """Describes the strategic texture of the community cards."""
    wetness: float        # 0.0 (dry) → 1.0 (very wet)
    flush_draw: bool      # True if 3+ cards of same suit
    straight_draw: bool   # True if 3+ connected cards (including gutshots)
    paired: bool          # True if board contains a pair
    high_card: int        # Highest community card rank value (or 0 if no board)


def analyze_board(community: List[Card]) -> BoardTexture:
    """
    Analyze community cards and return a BoardTexture.

    Works for any board size (0–5 cards); an empty board returns
    a neutral texture.
    """
    if not community:
        return BoardTexture(
            wetness=0.3,
            flush_draw=False,
            straight_draw=False,
            paired=False,
            high_card=0,
        )

    ranks = sorted([c.rank.value for c in community], reverse=True)
    suits = [c.suit for c in community]

    high_card = ranks[0] if ranks else 0

    # ── Flush draw (3+ same suit) ─────────────────────────────────────────────
    suit_counts = Counter(suits)
    flush_draw = max(suit_counts.values()) >= 3

    # ── Paired board ─────────────────────────────────────────────────────────
    rank_counts = Counter(ranks)
    paired = max(rank_counts.values()) >= 2

    # ── Straight draw (3+ connected within a 5-card window) ──────────────────
    unique_ranks = sorted(set(ranks))
    # Check for any 3 ranks within a span of 4 (open-ended or gutshot)
    straight_draw = _has_straight_draw(unique_ranks)

    # ── Wetness formula ───────────────────────────────────────────────────────
    wetness = (
        0.4 * float(flush_draw)
        + 0.4 * float(straight_draw)
        + 0.2 * float(paired)
    )
    # Clamp to [0, 1]
    wetness = max(0.0, min(1.0, wetness))

    return BoardTexture(
        wetness=wetness,
        flush_draw=flush_draw,
        straight_draw=straight_draw,
        paired=paired,
        high_card=high_card,
    )


def _has_straight_draw(unique_ranks: List[int]) -> bool:
    """
    Return True if there are at least 3 cards within any 5-card rank window.

    This catches open-ended straight draws (OESD) and gutshots.
    Also handles the Ace-low wheel draw (A-2-3-4-5).
    """
    if len(unique_ranks) < 3:
        return False

    # Add Ace as 1 for wheel draw detection
    extended = list(unique_ranks)
    if 14 in extended:
        extended.append(1)
    extended = sorted(set(extended))

    # Slide a 5-rank window and count unique ranks inside.
    # The window can start as low as (min - 4) to cover boards like J-Q-K
    # where the 9-K or T-A window catches the draw.
    lo_start = max(1, min(extended) - 4)
    hi_end = max(extended) + 1
    for low in range(lo_start, hi_end):
        high = low + 4  # window spans 5 ranks: low..low+4
        count = sum(1 for r in extended if low <= r <= high)
        if count >= 3:
            return True

    return False

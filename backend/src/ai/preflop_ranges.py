"""
Pre-flop range tables for 6-max Texas Hold'em.

Provides position-based open-raise and call frequencies derived from
standard GTO 6-max ranges (solver-approximated).

No external dependencies — all data is inlined as dicts.
"""
from __future__ import annotations

import logging
from typing import Any

from ..engine import Card, Rank

logger = logging.getLogger(__name__)

# ─── Hand combo helpers ────────────────────────────────────────────────────────

def get_hand_combo(c1: Card, c2: Card) -> str:
    """
    Return a canonical hand combo string.

    Examples: 'AA', 'AKs', 'T9o', '72o'
    - Pairs: just the rank twice, e.g. 'QQ'
    - Suited: higher rank first + 's', e.g. 'AKs'
    - Offsuit: higher rank first + 'o', e.g. 'AKo'
    """
    r1, r2 = c1.rank.value, c2.rank.value
    # Ensure higher rank comes first
    if r1 < r2:
        r1, r2 = r2, r1
        c1, c2 = c2, c1

    rank_char = {14: 'A', 13: 'K', 12: 'Q', 11: 'J', 10: 'T',
                 9: '9', 8: '8', 7: '7', 6: '6', 5: '5',
                 4: '4', 3: '3', 2: '2'}

    s1 = rank_char.get(r1, str(r1))
    s2 = rank_char.get(r2, str(r2))

    if r1 == r2:
        return s1 + s2           # pair: 'AA', 'TT', etc.
    suited = c1.suit == c2.suit
    return s1 + s2 + ('s' if suited else 'o')


def get_position(player_idx: int, dealer_idx: int, total: int) -> str:
    """
    Return position name for a player relative to the dealer button.

    Positions for 6-max (6 players):
      0 seats from dealer → BTN
      1 seat  from dealer → SB
      2 seats from dealer → BB
      3 seats from dealer → EP  (UTG)
      4 seats from dealer → MP  (HJ)
      5 seats from dealer → CO

    For fewer players the table is compressed accordingly.
    """
    offset = (player_idx - dealer_idx) % total
    if total >= 6:
        mapping = {0: 'BTN', 1: 'SB', 2: 'BB', 3: 'EP', 4: 'MP', 5: 'CO'}
    elif total == 5:
        mapping = {0: 'BTN', 1: 'SB', 2: 'BB', 3: 'EP', 4: 'CO'}
    elif total == 4:
        mapping = {0: 'BTN', 1: 'SB', 2: 'BB', 3: 'CO'}
    elif total == 3:
        mapping = {0: 'BTN', 1: 'SB', 2: 'BB'}
    else:
        mapping = {0: 'BTN', 1: 'BB'}
    return mapping.get(offset, 'EP')


# ─── Range data ────────────────────────────────────────────────────────────────
# Format: combo -> open-raise frequency (0.0–1.0)
# Based on standard 6-max GTO solver approximations.
# Combos not listed default to 0.0.

# BTN (Button) — widest range, ~65% of hands
_BTN_OPEN: dict[str, float] = {
    # Pairs
    'AA': 1.0, 'KK': 1.0, 'QQ': 1.0, 'JJ': 1.0, 'TT': 1.0,
    '99': 1.0, '88': 1.0, '77': 1.0, '66': 1.0, '55': 1.0,
    '44': 1.0, '33': 0.9, '22': 0.85,
    # Ax suited
    'AKs': 1.0, 'AQs': 1.0, 'AJs': 1.0, 'ATs': 1.0,
    'A9s': 1.0, 'A8s': 1.0, 'A7s': 1.0, 'A6s': 1.0,
    'A5s': 1.0, 'A4s': 1.0, 'A3s': 1.0, 'A2s': 1.0,
    # Kx suited
    'KQs': 1.0, 'KJs': 1.0, 'KTs': 1.0, 'K9s': 1.0,
    'K8s': 0.8, 'K7s': 0.7, 'K6s': 0.6, 'K5s': 0.55,
    # Qx suited
    'QJs': 1.0, 'QTs': 1.0, 'Q9s': 0.9, 'Q8s': 0.7, 'Q7s': 0.5,
    # Jx suited
    'JTs': 1.0, 'J9s': 0.9, 'J8s': 0.7, 'J7s': 0.5,
    # Tx suited
    'T9s': 1.0, 'T8s': 0.85, 'T7s': 0.6,
    # Connectors suited
    '98s': 1.0, '97s': 0.75, '87s': 0.9, '86s': 0.6,
    '76s': 0.9, '75s': 0.55, '65s': 0.85, '64s': 0.4,
    '54s': 0.75, '53s': 0.4, '43s': 0.5, '42s': 0.35,
    '32s': 0.3,
    # Ax offsuit
    'AKo': 1.0, 'AQo': 1.0, 'AJo': 1.0, 'ATo': 1.0,
    'A9o': 0.9, 'A8o': 0.75, 'A7o': 0.6, 'A6o': 0.5,
    'A5o': 0.7, 'A4o': 0.6, 'A3o': 0.5, 'A2o': 0.4,
    # Kx offsuit
    'KQo': 1.0, 'KJo': 1.0, 'KTo': 0.9, 'K9o': 0.7,
    'K8o': 0.5, 'K7o': 0.4,
    # Qx offsuit
    'QJo': 0.9, 'QTo': 0.75, 'Q9o': 0.55,
    # Jx offsuit
    'JTo': 0.8, 'J9o': 0.55,
    # Tx offsuit
    'T9o': 0.65, 'T8o': 0.45,
    # Misc
    '98o': 0.55, '87o': 0.4,
}

# CO (Cutoff) — ~50% of hands
_CO_OPEN: dict[str, float] = {
    'AA': 1.0, 'KK': 1.0, 'QQ': 1.0, 'JJ': 1.0, 'TT': 1.0,
    '99': 1.0, '88': 1.0, '77': 1.0, '66': 0.9, '55': 0.8,
    '44': 0.7, '33': 0.6, '22': 0.5,
    'AKs': 1.0, 'AQs': 1.0, 'AJs': 1.0, 'ATs': 1.0,
    'A9s': 1.0, 'A8s': 0.9, 'A7s': 0.8, 'A6s': 0.7,
    'A5s': 1.0, 'A4s': 0.9, 'A3s': 0.8, 'A2s': 0.7,
    'KQs': 1.0, 'KJs': 1.0, 'KTs': 1.0, 'K9s': 0.9,
    'K8s': 0.7, 'K7s': 0.55,
    'QJs': 1.0, 'QTs': 1.0, 'Q9s': 0.8, 'Q8s': 0.55,
    'JTs': 1.0, 'J9s': 0.8, 'J8s': 0.55,
    'T9s': 1.0, 'T8s': 0.75,
    '98s': 0.9, '87s': 0.8, '76s': 0.75, '65s': 0.7,
    '54s': 0.65, '43s': 0.4,
    'AKo': 1.0, 'AQo': 1.0, 'AJo': 1.0, 'ATo': 0.9,
    'A9o': 0.75, 'A8o': 0.6, 'A7o': 0.45, 'A5o': 0.55,
    'KQo': 1.0, 'KJo': 0.9, 'KTo': 0.75, 'K9o': 0.5,
    'QJo': 0.8, 'QTo': 0.6, 'Q9o': 0.4,
    'JTo': 0.7, 'J9o': 0.45,
    'T9o': 0.5, '98o': 0.4,
}

# MP (Middle position / HJ) — ~35%
_MP_OPEN: dict[str, float] = {
    'AA': 1.0, 'KK': 1.0, 'QQ': 1.0, 'JJ': 1.0, 'TT': 1.0,
    '99': 1.0, '88': 0.9, '77': 0.8, '66': 0.6, '55': 0.5,
    '44': 0.35, '33': 0.25, '22': 0.2,
    'AKs': 1.0, 'AQs': 1.0, 'AJs': 1.0, 'ATs': 1.0,
    'A9s': 0.9, 'A8s': 0.75, 'A7s': 0.6, 'A6s': 0.5,
    'A5s': 0.8, 'A4s': 0.7, 'A3s': 0.55, 'A2s': 0.45,
    'KQs': 1.0, 'KJs': 1.0, 'KTs': 0.9, 'K9s': 0.7,
    'K8s': 0.5,
    'QJs': 1.0, 'QTs': 0.9, 'Q9s': 0.65,
    'JTs': 0.9, 'J9s': 0.65,
    'T9s': 0.85, 'T8s': 0.55,
    '98s': 0.75, '87s': 0.6, '76s': 0.55, '65s': 0.45,
    'AKo': 1.0, 'AQo': 1.0, 'AJo': 0.9, 'ATo': 0.75,
    'A9o': 0.55, 'A8o': 0.4,
    'KQo': 0.9, 'KJo': 0.75, 'KTo': 0.55,
    'QJo': 0.65, 'QTo': 0.45,
    'JTo': 0.55,
}

# EP (Early position / UTG) — ~22%
_EP_OPEN: dict[str, float] = {
    'AA': 1.0, 'KK': 1.0, 'QQ': 1.0, 'JJ': 1.0, 'TT': 1.0,
    '99': 0.9, '88': 0.75, '77': 0.55, '66': 0.35, '55': 0.25,
    '44': 0.15, '33': 0.1, '22': 0.1,
    'AKs': 1.0, 'AQs': 1.0, 'AJs': 1.0, 'ATs': 0.9,
    'A9s': 0.7, 'A8s': 0.55, 'A7s': 0.4, 'A5s': 0.6, 'A4s': 0.45,
    'A3s': 0.35, 'A2s': 0.25,
    'KQs': 1.0, 'KJs': 0.9, 'KTs': 0.75, 'K9s': 0.5,
    'QJs': 0.85, 'QTs': 0.7,
    'JTs': 0.8, 'J9s': 0.5,
    'T9s': 0.65, 'T8s': 0.4,
    '98s': 0.55, '87s': 0.4, '76s': 0.35,
    'AKo': 1.0, 'AQo': 0.95, 'AJo': 0.75, 'ATo': 0.55,
    'A9o': 0.35,
    'KQo': 0.8, 'KJo': 0.6, 'KTo': 0.4,
    'QJo': 0.5, 'QTo': 0.3,
    'JTo': 0.4,
}

# SB (Small blind) — complex (includes limp), simplified as open freq ~45%
_SB_OPEN: dict[str, float] = {
    'AA': 1.0, 'KK': 1.0, 'QQ': 1.0, 'JJ': 1.0, 'TT': 1.0,
    '99': 1.0, '88': 1.0, '77': 0.9, '66': 0.8, '55': 0.75,
    '44': 0.65, '33': 0.55, '22': 0.5,
    'AKs': 1.0, 'AQs': 1.0, 'AJs': 1.0, 'ATs': 1.0,
    'A9s': 0.9, 'A8s': 0.8, 'A7s': 0.7, 'A6s': 0.65,
    'A5s': 1.0, 'A4s': 0.9, 'A3s': 0.8, 'A2s': 0.7,
    'KQs': 1.0, 'KJs': 1.0, 'KTs': 0.95, 'K9s': 0.8,
    'K8s': 0.65, 'K7s': 0.55, 'K6s': 0.45,
    'QJs': 1.0, 'QTs': 0.95, 'Q9s': 0.8, 'Q8s': 0.6,
    'JTs': 1.0, 'J9s': 0.85, 'J8s': 0.6,
    'T9s': 0.95, 'T8s': 0.75, 'T7s': 0.5,
    '98s': 0.85, '87s': 0.75, '76s': 0.7, '65s': 0.65,
    '54s': 0.6, '43s': 0.45,
    'AKo': 1.0, 'AQo': 1.0, 'AJo': 0.95, 'ATo': 0.85,
    'A9o': 0.7, 'A8o': 0.6, 'A7o': 0.5, 'A5o': 0.65, 'A4o': 0.55,
    'KQo': 1.0, 'KJo': 0.9, 'KTo': 0.75, 'K9o': 0.55,
    'QJo': 0.8, 'QTo': 0.65, 'Q9o': 0.45,
    'JTo': 0.7, 'J9o': 0.5,
    'T9o': 0.6, '98o': 0.45,
}

# BB (Big blind) — defense frequency vs single raise (~55% calls/3-bets)
# Listed as CALL frequency when facing a single open raise
_BB_CALL: dict[str, float] = {
    'AA': 0.0,  # always 3-bet (handled separately)
    'KK': 0.0, 'QQ': 0.0, 'JJ': 0.0,  # mostly 3-bet
    'TT': 0.7, '99': 0.8, '88': 0.85, '77': 0.9, '66': 0.9,
    '55': 0.85, '44': 0.8, '33': 0.75, '22': 0.7,
    'AKs': 0.0, 'AQs': 0.0,  # 3-bet
    'AJs': 0.85, 'ATs': 0.9, 'A9s': 0.9, 'A8s': 0.85,
    'A7s': 0.8, 'A6s': 0.75, 'A5s': 0.9, 'A4s': 0.85, 'A3s': 0.8, 'A2s': 0.75,
    'KQs': 0.85, 'KJs': 0.9, 'KTs': 0.9, 'K9s': 0.85, 'K8s': 0.7,
    'QJs': 0.9, 'QTs': 0.9, 'Q9s': 0.8, 'Q8s': 0.65,
    'JTs': 0.9, 'J9s': 0.8, 'J8s': 0.65,
    'T9s': 0.85, 'T8s': 0.75, 'T7s': 0.55,
    '98s': 0.8, '97s': 0.65, '87s': 0.75, '86s': 0.55,
    '76s': 0.7, '75s': 0.5, '65s': 0.65, '54s': 0.6,
    'AKo': 0.2, 'AQo': 0.5, 'AJo': 0.8, 'ATo': 0.85,
    'A9o': 0.75, 'A8o': 0.65, 'A7o': 0.55, 'A5o': 0.65,
    'KQo': 0.8, 'KJo': 0.8, 'KTo': 0.75, 'K9o': 0.6,
    'QJo': 0.75, 'QTo': 0.65, 'Q9o': 0.5,
    'JTo': 0.7, 'J9o': 0.55,
    'T9o': 0.6, '98o': 0.5, '87o': 0.4,
}

# Open-raise tables indexed by position
_OPEN_TABLES: dict[str, dict[str, float]] = {
    'BTN': _BTN_OPEN,
    'CO':  _CO_OPEN,
    'MP':  _MP_OPEN,
    'EP':  _EP_OPEN,
    'SB':  _SB_OPEN,
    'BB':  {},  # BB doesn't open-raise (posts)
}

# Call-vs-raise tables (facing a single open from any position)
# Simplified: EP/MP/CO/BTN call ~same range when OOP
_CALL_VS_RAISE: dict[str, float] = {
    'AA': 0.0, 'KK': 0.0, 'QQ': 0.05,  # 3-bet these
    'JJ': 0.4, 'TT': 0.7, '99': 0.8, '88': 0.85, '77': 0.85,
    '66': 0.8, '55': 0.7, '44': 0.6, '33': 0.5, '22': 0.4,
    'AKs': 0.0, 'AQs': 0.3, 'AJs': 0.7, 'ATs': 0.8,
    'A9s': 0.75, 'A8s': 0.7, 'A7s': 0.6, 'A6s': 0.5,
    'A5s': 0.8, 'A4s': 0.7, 'A3s': 0.6, 'A2s': 0.5,
    'KQs': 0.65, 'KJs': 0.75, 'KTs': 0.8, 'K9s': 0.65,
    'QJs': 0.75, 'QTs': 0.75, 'Q9s': 0.6,
    'JTs': 0.8, 'J9s': 0.65, 'J8s': 0.5,
    'T9s': 0.75, 'T8s': 0.6,
    '98s': 0.65, '87s': 0.55, '76s': 0.5, '65s': 0.45,
    'AKo': 0.15, 'AQo': 0.6, 'AJo': 0.7, 'ATo': 0.65,
    'A9o': 0.5, 'A8o': 0.4,
    'KQo': 0.6, 'KJo': 0.6, 'KTo': 0.45,
    'QJo': 0.55, 'QTo': 0.4,
    'JTo': 0.5,
}


# ─── Public API ────────────────────────────────────────────────────────────────

def preflop_open_freq(combo: str, position: str) -> float:
    """
    Return the open-raise frequency for the given combo and position.

    Returns 0.0 for combos / positions not in the table.
    """
    table = _OPEN_TABLES.get(position, {})
    return table.get(combo, 0.0)


def preflop_call_freq(combo: str, position: str) -> float:
    """
    Return the call (vs single raise) frequency for the given combo.

    BB uses the BB-specific defence table; all other positions use the
    generic call-vs-raise table.
    """
    if position == 'BB':
        return _BB_CALL.get(combo, 0.0)
    return _CALL_VS_RAISE.get(combo, 0.0)

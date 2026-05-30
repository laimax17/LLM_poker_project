"""
Spot analytics for the LLM agent.

Pre-computes the quantitative facts a strong player would work out before
acting — equity, pot odds, position, board texture, stack depth — using the
existing offline tools. The agent is then asked to *reason over* these numbers
rather than estimate them itself, which is both cheaper (one LLM call) and far
more accurate than letting the model guess equities.
"""
from __future__ import annotations

import logging
from typing import Any, List, Optional

from ..engine import Card, Rank, Suit
from .board_texture import analyze_board
from .equity import estimate_equity
from .preflop_ranges import get_hand_combo, get_position, preflop_open_freq, preflop_call_freq

logger = logging.getLogger(__name__)

# Monte-Carlo sims for bot equity — modest, to keep turns snappy.
BOT_EQUITY_SIMS = 200

_RANK_CHAR = {
    14: 'A', 13: 'K', 12: 'Q', 11: 'J', 10: 'T',
    9: '9', 8: '8', 7: '7', 6: '6', 5: '5', 4: '4', 3: '3', 2: '2',
}
_SUIT_CHAR = {'Hearts': '♥', 'Diamonds': '♦', 'Clubs': '♣', 'Spades': '♠'}


def _to_card(d: Optional[dict[str, Any]]) -> Optional[Card]:
    if not d:
        return None
    try:
        return Card(rank=Rank(int(d['rank'])), suit=Suit(str(d['suit'])))
    except (KeyError, ValueError, TypeError):
        return None


def _parse(cards: List[Optional[dict[str, Any]]]) -> List[Card]:
    return [c for c in (_to_card(d) for d in (cards or [])) if c is not None]


def card_str(card: Card) -> str:
    r = _RANK_CHAR.get(card.rank.value, str(card.rank.value))
    s = _SUIT_CHAR.get(card.suit.value, card.suit.value[:1])
    return f'{r}{s}'


_POSITION_LABEL = {
    'BTN': 'BTN (button, in position)',
    'CO': 'CO (cutoff, late)',
    'MP': 'MP (middle)',
    'EP': 'EP (early, out of position)',
    'SB': 'SB (small blind, OOP)',
    'BB': 'BB (big blind, OOP)',
}


def compute_analytics(game_state: dict[str, Any], player_id: str) -> dict[str, Any]:
    """Return a dict of pre-computed quantitative facts for the spot."""
    players: List[dict[str, Any]] = game_state.get('players', [])
    me = next((p for p in players if p.get('id') == player_id), None)
    if me is None:
        return {}

    street = str(game_state.get('state', 'PREFLOP'))
    pot = int(game_state.get('pot', 0))
    current_bet = int(game_state.get('current_bet', 0))
    my_bet = int(me.get('current_bet', 0))
    to_call = max(0, current_bet - my_bet)
    my_chips = int(me.get('chips', 0))

    hand = _parse(me.get('hand', []))
    board = _parse(game_state.get('community_cards', []))

    opponents = [p for p in players if p.get('id') != player_id]
    active_opponents = sum(1 for p in opponents if p.get('is_active'))

    # Position
    dealer_idx = next((i for i, p in enumerate(players) if p.get('is_dealer')), 0)
    my_idx = next((i for i, p in enumerate(players) if p.get('id') == player_id), 0)
    position = get_position(my_idx, dealer_idx, len(players)) if players else 'MP'

    pot_odds = to_call / (pot + to_call) if to_call > 0 else 0.0

    out: dict[str, Any] = {
        'street': street,
        'position': position,
        'position_label': _POSITION_LABEL.get(position, position),
        'hand_str': ' '.join(card_str(c) for c in hand) if hand else '??',
        'board_str': ' '.join(card_str(c) for c in board) if board else '(none)',
        'pot': pot,
        'to_call': to_call,
        'pot_odds': pot_odds,
        'my_chips': my_chips,
        'min_raise': int(game_state.get('min_raise', 20)),
        'active_opponents': active_opponents,
        'raise_count': int(game_state.get('raise_count', 0)),
    }

    if len(hand) == 2:
        out['combo'] = get_hand_combo(hand[0], hand[1])

    if street == 'PREFLOP' and len(hand) == 2:
        out['open_freq'] = preflop_open_freq(out['combo'], position)
        out['call_freq'] = preflop_call_freq(out['combo'], position)

    if street != 'PREFLOP' and len(hand) == 2:
        equity = estimate_equity(hand, board, max(1, active_opponents), n_sim=BOT_EQUITY_SIMS)
        texture = analyze_board(board)
        draws = []
        if texture.flush_draw:
            draws.append('flush draw')
        if texture.straight_draw:
            draws.append('straight draw')
        if texture.paired:
            draws.append('paired board')
        out['equity'] = equity
        out['board_wetness'] = texture.wetness
        out['board_draws'] = draws or ['dry']

    return out

"""
Pseudo-GTO bot strategy for Texas Hold'em.

Pre-flop  : position-based range tables with mixed-frequency decisions.
Post-flop : Monte Carlo equity + board texture → geometric bet sizing + GTO bluff freq.

No external poker library required.
"""
from __future__ import annotations

import logging
import random
from typing import Any, List, Optional

from ..engine import Card, Rank, Suit
from ..schemas import AIThought
from .strategy import BotStrategy
from .preflop_ranges import get_hand_combo, get_position, preflop_open_freq, preflop_call_freq
from .equity import estimate_equity
from .board_texture import analyze_board, BoardTexture

logger = logging.getLogger(__name__)

# ─── Chat message pools ───────────────────────────────────────────────────────

_CHAT: dict[str, List[str]] = {
    'fold':  [
        'Not my spot.', 'I fold.', 'Bad equity.', 'Range disadvantage.',
        'Folding this one.', 'Not profitable here.',
    ],
    'check': [
        'Checking.', 'I check.', 'Pot control.', 'Taking a free card.',
        'Check.', 'Checking my option.',
    ],
    'call':  [
        'Call.', 'I call.', "I've got the odds.", 'Calling.',
        'Price is right.', 'Pot odds check out.',
    ],
    'raise': [
        'Raise.', 'I raise.', "I'm ahead here.", 'Value bet.',
        'Geometric sizing.', 'Building the pot.', 'Let\'s play.',
    ],
}


def _chat(action: str) -> str:
    return random.choice(_CHAT.get(action, ['...']))


# ─── Card reconstruction from game-state dicts ───────────────────────────────

def _dict_to_card(d: Optional[dict[str, Any]]) -> Optional[Card]:
    """Convert a card dict {'rank': int, 'suit': str} to a Card object."""
    if d is None:
        return None
    try:
        rank = Rank(int(d['rank']))
        suit = Suit(str(d['suit']))
        return Card(rank=rank, suit=suit)
    except (KeyError, ValueError) as exc:
        logger.debug('_dict_to_card failed: %s — %s', d, exc)
        return None


def _parse_hand(hand_raw: List[Optional[dict[str, Any]]]) -> List[Card]:
    """Parse a list of card dicts (may contain None) into Card objects."""
    result: List[Card] = []
    for d in hand_raw:
        card = _dict_to_card(d)
        if card is not None:
            result.append(card)
    return result


# ─── Strategy ─────────────────────────────────────────────────────────────────

class GTOBotStrategy(BotStrategy):
    """
    Pseudo-GTO bot strategy.

    Pre-flop decisions use position-based RFI and call frequency tables.
    Post-flop decisions use Monte Carlo equity, board texture analysis,
    and GTO-balanced bet sizing / bluff frequencies.
    """

    # Number of Monte Carlo simulations per decision
    N_SIM_POSTFLOP: int = 300

    def decide(self, game_state: dict[str, Any], player_id: str) -> AIThought:
        """Main entry: dispatch to pre- or post-flop logic."""
        street: str = game_state.get('state', 'PREFLOP')
        players: List[dict[str, Any]] = game_state.get('players', [])

        me = next((p for p in players if p['id'] == player_id), None)
        if me is None:
            logger.warning('GTOBotStrategy: player %s not found in state', player_id)
            return AIThought(action='fold', amount=0, thought='player not found', chat_message='Fold.')

        my_hand = _parse_hand(me.get('hand', []))
        if not my_hand:
            # No visible hand (shouldn't happen for the bot itself)
            return AIThought(action='fold', amount=0, thought='no hand', chat_message='Fold.')

        community_raw: List[dict[str, Any]] = game_state.get('community_cards', [])
        community = _parse_hand(community_raw)

        active_players = [p for p in players if p.get('is_active') and not p.get('is_all_in')]
        active_opponents = max(0, len(active_players) - 1)

        pot: int = game_state.get('pot', 0)
        current_bet: int = game_state.get('current_bet', 0)
        min_raise: int = game_state.get('min_raise', 20)
        my_bet: int = me.get('current_bet', 0)
        my_chips: int = me.get('chips', 0)
        to_call: int = max(0, current_bet - my_bet)
        can_check: bool = to_call == 0

        # Find dealer index
        dealer_idx = next(
            (i for i, p in enumerate(players) if p.get('is_dealer')), 0
        )
        my_idx = next((i for i, p in enumerate(players) if p['id'] == player_id), 0)
        position = get_position(my_idx, dealer_idx, len(players))

        if street == 'PREFLOP':
            return self._decide_preflop(
                my_hand=my_hand,
                position=position,
                to_call=to_call,
                can_check=can_check,
                pot=pot,
                min_raise=min_raise,
                my_chips=my_chips,
            )
        else:
            return self._decide_postflop(
                my_hand=my_hand,
                community=community,
                active_opponents=active_opponents,
                to_call=to_call,
                can_check=can_check,
                pot=pot,
                min_raise=min_raise,
                my_chips=my_chips,
            )

    # ── Pre-flop ──────────────────────────────────────────────────────────────

    def _decide_preflop(
        self,
        my_hand: List[Card],
        position: str,
        to_call: int,
        can_check: bool,
        pot: int,
        min_raise: int,
        my_chips: int,
    ) -> AIThought:
        combo = get_hand_combo(my_hand[0], my_hand[1])
        open_f = preflop_open_freq(combo, position)
        call_f = preflop_call_freq(combo, position)

        # BB special case: no open-raise needed (already posted)
        if position == 'BB' and can_check:
            # BB can squeeze with 3-bet hands or check
            if open_f > 0.7 and random.random() < 0.4:
                raise_amount = min(min_raise * 3, my_chips)
                if raise_amount > 0:
                    return AIThought(
                        action='raise', amount=raise_amount,
                        thought=f'BB squeeze: {combo} ({open_f:.0%} freq)',
                        chat_message=_chat('raise'),
                    )
            return AIThought(
                action='check', amount=0,
                thought=f'BB check: {combo}',
                chat_message=_chat('check'),
            )

        if can_check:
            # Nobody has raised — decide whether to open-raise
            if open_f > 0 and random.random() < open_f:
                # Standard open: 2.5× BB (big_blind ≈ min_raise here)
                raise_amount = min(min_raise * 2 + (min_raise // 2), my_chips)
                raise_amount = max(raise_amount, min_raise)
                return AIThought(
                    action='raise', amount=raise_amount,
                    thought=f'Open raise: {combo} at {position} ({open_f:.0%})',
                    chat_message=_chat('raise'),
                )
            return AIThought(
                action='check', amount=0,
                thought=f'Check behind: {combo} at {position}',
                chat_message=_chat('check'),
            )
        else:
            # There is a raise to face
            if to_call >= my_chips:
                # All-in or fold decision
                if call_f > 0 and random.random() < call_f * 0.5:
                    return AIThought(
                        action='call', amount=0,
                        thought=f'All-in call: {combo}',
                        chat_message=_chat('call'),
                    )
                return AIThought(
                    action='fold', amount=0,
                    thought=f'Fold to all-in: {combo}',
                    chat_message=_chat('fold'),
                )

            # 3-bet opportunity: strong hands get aggressive
            three_bet_f = max(0.0, open_f - 0.5)  # only widest openers 3-bet
            if three_bet_f > 0 and random.random() < three_bet_f * 0.4:
                raise_amount = min(to_call * 3, my_chips)
                raise_amount = max(raise_amount, min_raise)
                return AIThought(
                    action='raise', amount=raise_amount,
                    thought=f'3-bet: {combo} at {position} (3bet freq {three_bet_f:.0%})',
                    chat_message=_chat('raise'),
                )

            if call_f > 0 and random.random() < call_f:
                return AIThought(
                    action='call', amount=0,
                    thought=f'Call raise: {combo} at {position} ({call_f:.0%})',
                    chat_message=_chat('call'),
                )

            return AIThought(
                action='fold', amount=0,
                thought=f'Fold pre-flop: {combo} at {position} (call_f={call_f:.0%})',
                chat_message=_chat('fold'),
            )

    # ── Post-flop ─────────────────────────────────────────────────────────────

    def _decide_postflop(
        self,
        my_hand: List[Card],
        community: List[Card],
        active_opponents: int,
        to_call: int,
        can_check: bool,
        pot: int,
        min_raise: int,
        my_chips: int,
    ) -> AIThought:
        # Monte Carlo equity estimation
        num_opp = max(1, active_opponents)
        equity = estimate_equity(my_hand, community, num_opp, n_sim=self.N_SIM_POSTFLOP)

        # Board texture
        texture: BoardTexture = analyze_board(community)

        # Pot odds (how much equity we need to profitably call)
        if to_call > 0:
            pot_odds = to_call / (pot + to_call + 1e-6)
        else:
            pot_odds = 0.0

        # ── Bet sizing based on texture ──────────────────────────────────────
        # Dry boards → smaller sizing; wet boards → larger sizing
        if texture.wetness >= 0.5:
            bet_fraction = 0.66  # 2/3 pot on wet boards
            value_threshold = 0.70
        else:
            bet_fraction = 0.33  # 1/3 pot on dry boards
            value_threshold = 0.65

        bet_size = max(int(pot * bet_fraction), min_raise)
        bet_size = min(bet_size, my_chips)

        # GTO bluff frequency: bet_size / (pot + 2 * bet_size)
        bluff_freq = bet_size / (pot + 2 * bet_size + 1e-6)

        thought_base = (
            f'equity={equity:.0%} pot_odds={pot_odds:.0%} '
            f'wet={texture.wetness:.2f} bluff_f={bluff_freq:.0%}'
        )

        # ── Decision tree ────────────────────────────────────────────────────
        if can_check:
            # No bet to face
            if equity >= value_threshold:
                # Value bet
                return AIThought(
                    action='raise', amount=bet_size,
                    thought=f'Value bet: {thought_base}',
                    chat_message=_chat('raise'),
                )
            if equity < 0.30 and random.random() < bluff_freq:
                # Bluff with balanced frequency
                return AIThought(
                    action='raise', amount=bet_size,
                    thought=f'Bluff: {thought_base}',
                    chat_message=_chat('raise'),
                )
            return AIThought(
                action='check', amount=0,
                thought=f'Check: {thought_base}',
                chat_message=_chat('check'),
            )
        else:
            # Facing a bet
            if equity >= value_threshold and equity > pot_odds + 0.10:
                # Re-raise for value
                re_raise = min(int(pot * bet_fraction * 1.5), my_chips)
                re_raise = max(re_raise, min_raise)
                if re_raise <= to_call or my_chips <= to_call:
                    # Not enough chips to raise — just call
                    return AIThought(
                        action='call', amount=0,
                        thought=f'Call (value): {thought_base}',
                        chat_message=_chat('call'),
                    )
                return AIThought(
                    action='raise', amount=re_raise,
                    thought=f'Value raise: {thought_base}',
                    chat_message=_chat('raise'),
                )

            if equity > pot_odds + 0.08:
                # Profitable call by equity
                return AIThought(
                    action='call', amount=0,
                    thought=f'Call (odds): {thought_base}',
                    chat_message=_chat('call'),
                )

            if equity > pot_odds and random.random() < 0.35:
                # Marginal call — mixed strategy
                return AIThought(
                    action='call', amount=0,
                    thought=f'Marginal call: {thought_base}',
                    chat_message=_chat('call'),
                )

            if equity < 0.20 and random.random() < bluff_freq * 0.5:
                # Bluff raise even when facing a bet (semi-bluff territory)
                bluff_raise = min(int(pot * 0.66), my_chips)
                bluff_raise = max(bluff_raise, min_raise)
                if bluff_raise > to_call and my_chips > to_call:
                    return AIThought(
                        action='raise', amount=bluff_raise,
                        thought=f'Semi-bluff raise: {thought_base}',
                        chat_message=_chat('raise'),
                    )

            return AIThought(
                action='fold', amount=0,
                thought=f'Fold: {thought_base}',
                chat_message=_chat('fold'),
            )

"""
Pseudo-GTO bot strategy for Texas Hold'em, with per-personality modifiers.

Pre-flop  : position-based range tables with mixed-frequency decisions.
            Uses raise_count to correctly distinguish "open raise" from "facing a raise".
Post-flop : Monte Carlo equity + board texture → geometric bet sizing + GTO bluff freq.
            Personality shifts thresholds so each bot has a distinct character.

No external poker library required.
"""
from __future__ import annotations

import logging
import random
from dataclasses import dataclass
from typing import Any, List, Optional

from ..engine import Card, Rank, Suit
from ..schemas import AIThought
from .strategy import BotStrategy
from .preflop_ranges import get_hand_combo, get_position, preflop_open_freq, preflop_call_freq
from .equity import estimate_equity
from .board_texture import analyze_board, BoardTexture
from .rule_based import PERSONALITIES, Personality, _chat as _personality_chat

logger = logging.getLogger(__name__)

# ─── GTO Constants ────────────────────────────────────────────────────────────

# Pre-flop: BB squeeze
_BB_SQUEEZE_OPEN_THRESH: float = 0.70  # open_f must exceed this for BB to consider squeeze
_BB_SQUEEZE_PROB: float = 0.40         # probability of executing the squeeze

# Pre-flop: all-in call and 3-bet frequencies
_ALLIN_CALL_FREQ_MULT: float = 0.50    # scales call_f for all-in decisions
_THREE_BET_OPEN_OFFSET: float = 0.50   # open_f must exceed this offset to enable 3-bet
_THREE_BET_FREQ_MULT: float = 0.40     # scales the 3-bet probability

# Post-flop: board-texture thresholds for bet sizing
_WETNESS_THRESHOLD: float = 0.50       # wetness ≥ this → use larger sizing

# Post-flop: pot fractions per board texture
_WET_BET_FRAC: float = 0.66            # 2/3 pot on wet boards
_DRY_BET_FRAC: float = 0.33            # 1/3 pot on dry boards

# Post-flop: base equity thresholds (before personality offset)
_WET_VALUE_THRESH: float = 0.70        # equity needed to value-bet on wet boards
_DRY_VALUE_THRESH: float = 0.65        # equity needed to value-bet on dry boards
_BLUFF_EQUITY_THRESH: float = 0.30     # equity below which bot may bluff (when checking)
_SEMI_BLUFF_EQUITY_THRESH: float = 0.20  # equity below which semi-bluff raise is allowed

# Post-flop: base equity margins over pot odds
_VALUE_RAISE_MARGIN: float = 0.10      # equity must exceed pot_odds by this to value-raise
_CALL_MARGIN: float = 0.08             # equity must exceed pot_odds by this to call

# Post-flop: mixed strategy probability for marginal spots
_MARGINAL_CALL_PROB: float = 0.35      # frequency of marginal calls when equity barely > pot_odds


# ─── Personality modifier system ──────────────────────────────────────────────

@dataclass(frozen=True)
class _PersonalityMod:
    """Offsets/multipliers applied to GTO base thresholds per personality."""
    open_freq_mult: float      # multiply preflop open/call freq  (>1 = wider range)
    value_thresh_offset: float # add to value threshold           (negative = bets more aggressively)
    call_margin_offset: float  # add to call margin               (negative = calls more / folds less)
    bluff_freq_mult: float     # multiply GTO bluff frequency     (>1 = bluffs more)


_PERSONALITY_MODS: dict[str, _PersonalityMod] = {
    # shark: balanced GTO+, slightly elevated bluff frequency
    'shark':   _PersonalityMod(open_freq_mult=1.00, value_thresh_offset=0.00,
                               call_margin_offset=0.00, bluff_freq_mult=1.20),
    # rock: only opens top 70% of GTO range, bets with high equity only, almost never bluffs
    'rock':    _PersonalityMod(open_freq_mult=0.70, value_thresh_offset=0.06,
                               call_margin_offset=0.08, bluff_freq_mult=0.20),
    # maniac: 140% open range, value-bets with 12% less equity, hyper-aggressive bluffing
    'maniac':  _PersonalityMod(open_freq_mult=1.40, value_thresh_offset=-0.12,
                               call_margin_offset=-0.12, bluff_freq_mult=2.50),
    # station: normal range, very rarely bets, calls with 18% worse equity than GTO
    'station': _PersonalityMod(open_freq_mult=1.05, value_thresh_offset=0.02,
                               call_margin_offset=-0.18, bluff_freq_mult=0.40),
    # tag: tight-aggressive GTO-clone, slightly fewer bluffs
    'tag':     _PersonalityMod(open_freq_mult=1.00, value_thresh_offset=0.00,
                               call_margin_offset=0.00, bluff_freq_mult=0.80),
}

_DEFAULT_MOD = _PERSONALITY_MODS['shark']


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
    Pseudo-GTO bot strategy with personality-adjusted thresholds.

    Pre-flop decisions use position-based RFI and call frequency tables.
    raise_count from game state correctly distinguishes an open-raise opportunity
    from facing an actual raise (fixing the previous can_check-only bug).

    Post-flop decisions use Monte Carlo equity, board texture analysis,
    and GTO-balanced bet sizing / bluff frequencies, modulated by personality.
    """

    # Number of Monte Carlo simulations per decision
    N_SIM_POSTFLOP: int = 500

    def __init__(self, personality: str = 'shark') -> None:
        self._personality_name: str = personality
        self._mods: _PersonalityMod = _PERSONALITY_MODS.get(personality, _DEFAULT_MOD)
        self._p: Personality = PERSONALITIES.get(personality, PERSONALITIES['shark'])

    def decide(self, game_state: dict[str, Any], player_id: str, locale: str = 'en') -> AIThought:
        """Main entry: dispatch to pre- or post-flop logic."""
        street: str = game_state.get('state', 'PREFLOP')
        players: List[dict[str, Any]] = game_state.get('players', [])

        me = next((p for p in players if p['id'] == player_id), None)
        if me is None:
            logger.warning('GTOBotStrategy: player %s not found in state', player_id)
            return AIThought(action='fold', amount=0, thought='player not found',
                             chat_message=_personality_chat(self._p, 'fold', locale))

        my_hand = _parse_hand(me.get('hand', []))
        if not my_hand:
            return AIThought(action='fold', amount=0, thought='no hand',
                             chat_message=_personality_chat(self._p, 'fold', locale))

        community_raw: List[dict[str, Any]] = game_state.get('community_cards', [])
        community = _parse_hand(community_raw)

        active_players = [p for p in players if p.get('is_active') and not p.get('is_all_in')]
        active_opponents = max(0, len(active_players) - 1)

        pot: int = game_state.get('pot', 0)
        current_bet: int = game_state.get('current_bet', 0)
        min_raise: int = game_state.get('min_raise', 20)
        raise_count: int = game_state.get('raise_count', 0)
        my_bet: int = me.get('current_bet', 0)
        my_chips: int = me.get('chips', 0)
        to_call: int = max(0, current_bet - my_bet)
        can_check: bool = to_call == 0

        # Find dealer index for position calculation
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
                raise_count=raise_count,
                locale=locale,
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
                locale=locale,
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
        raise_count: int,
        locale: str = 'en',
    ) -> AIThought:
        combo = get_hand_combo(my_hand[0], my_hand[1])
        # Apply personality range multiplier (maniac opens wider, rock tighter)
        open_f = min(1.0, preflop_open_freq(combo, position) * self._mods.open_freq_mult)
        call_f = min(1.0, preflop_call_freq(combo, position) * self._mods.open_freq_mult)

        # ── CASE 1: BB with option to check (nobody has raised above the blind) ──
        if position == 'BB' and can_check:
            if open_f > _BB_SQUEEZE_OPEN_THRESH and random.random() < _BB_SQUEEZE_PROB:
                raise_amount = max(min_raise, min(min_raise * 3, my_chips))
                return AIThought(
                    action='raise', amount=raise_amount,
                    thought=f'BB squeeze: {combo} ({open_f:.0%} freq)',
                    chat_message=_personality_chat(self._p, 'raise', locale),
                )
            return AIThought(
                action='check', amount=0,
                thought=f'BB check: {combo}',
                chat_message=_personality_chat(self._p, 'check', locale),
            )

        # ── CASE 2: No raise yet — this is an open-raise opportunity ──────────
        # (raise_count == 0 means nobody has voluntarily raised above the blind)
        if raise_count == 0:
            if open_f > 0 and random.random() < open_f:
                # Standard open: 2.5× BB (min_raise ≈ BB when no raises have happened)
                raise_amount = max(min_raise, min(min_raise * 2 + min_raise // 2, my_chips))
                return AIThought(
                    action='raise', amount=raise_amount,
                    thought=f'Open raise: {combo} at {position} ({open_f:.0%})',
                    chat_message=_personality_chat(self._p, 'raise', locale),
                )
            # GTO preflop rarely limps; fold hands outside opening range
            return AIThought(
                action='fold', amount=0,
                thought=f'Fold pre-flop (outside range): {combo} at {position}',
                chat_message=_personality_chat(self._p, 'fold', locale),
            )

        # ── CASE 3: Facing an actual raise (raise_count >= 1) ─────────────────
        if to_call >= my_chips:
            # All-in or fold decision
            if call_f > 0 and random.random() < call_f * _ALLIN_CALL_FREQ_MULT:
                return AIThought(
                    action='call', amount=0,
                    thought=f'All-in call: {combo}',
                    chat_message=_personality_chat(self._p, 'call', locale),
                )
            return AIThought(
                action='fold', amount=0,
                thought=f'Fold to all-in: {combo}',
                chat_message=_personality_chat(self._p, 'fold', locale),
            )

        # 3-bet opportunity: strong hands get aggressive
        three_bet_f = max(0.0, open_f - _THREE_BET_OPEN_OFFSET)
        if three_bet_f > 0 and random.random() < three_bet_f * _THREE_BET_FREQ_MULT:
            raise_amount = max(min_raise, min(to_call * 3, my_chips))
            return AIThought(
                action='raise', amount=raise_amount,
                thought=f'3-bet: {combo} at {position} (3bet_f={three_bet_f:.0%})',
                chat_message=_personality_chat(self._p, 'raise', locale),
            )

        # Call with hands in calling range
        if call_f > 0 and random.random() < call_f:
            return AIThought(
                action='call', amount=0,
                thought=f'Call raise: {combo} at {position} ({call_f:.0%})',
                chat_message=_personality_chat(self._p, 'call', locale),
            )

        return AIThought(
            action='fold', amount=0,
            thought=f'Fold pre-flop: {combo} at {position} (call_f={call_f:.0%})',
            chat_message=_personality_chat(self._p, 'fold', locale),
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
        locale: str = 'en',
    ) -> AIThought:
        # Monte Carlo equity estimation
        num_opp = max(1, active_opponents)
        equity = estimate_equity(my_hand, community, num_opp, n_sim=self.N_SIM_POSTFLOP)

        # Board texture drives base bet sizing and value threshold
        texture: BoardTexture = analyze_board(community)

        # Pot odds (minimum equity needed to break even on a call)
        pot_odds = to_call / (pot + to_call + 1e-6) if to_call > 0 else 0.0

        # ── Board-texture base thresholds ────────────────────────────────────
        if texture.wetness >= _WETNESS_THRESHOLD:
            bet_fraction = _WET_BET_FRAC       # 2/3 pot on wet boards
            base_value_thresh = _WET_VALUE_THRESH
        else:
            bet_fraction = _DRY_BET_FRAC       # 1/3 pot on dry boards
            base_value_thresh = _DRY_VALUE_THRESH

        # ── Apply personality modifiers ───────────────────────────────────────
        value_threshold = base_value_thresh + self._mods.value_thresh_offset
        call_margin = _CALL_MARGIN + self._mods.call_margin_offset
        value_raise_margin = _VALUE_RAISE_MARGIN + self._mods.call_margin_offset

        # Bet size: clamped to [min_raise, my_chips]
        bet_size = max(int(pot * bet_fraction), min_raise)
        bet_size = min(bet_size, my_chips)

        # GTO bluff frequency with personality multiplier
        raw_bluff_freq = bet_size / (pot + 2 * bet_size + 1e-6)
        bluff_freq = min(1.0, raw_bluff_freq * self._mods.bluff_freq_mult)

        thought_base = (
            f'[{self._personality_name}] equity={equity:.0%} pot_odds={pot_odds:.0%} '
            f'wet={texture.wetness:.2f} val_thresh={value_threshold:.2f} bluff_f={bluff_freq:.0%}'
        )

        logger.debug(
            'GTOBot[%s]: %s equity=%.2f pot_odds=%.2f wet=%.2f val_thresh=%.2f',
            self._personality_name, 'check' if can_check else f'face {to_call}',
            equity, pot_odds, texture.wetness, value_threshold,
        )

        # ── Decision tree ────────────────────────────────────────────────────
        if can_check:
            # No bet to face — decide whether to bet or check
            if equity >= value_threshold:
                # Value bet
                return AIThought(
                    action='raise', amount=bet_size,
                    thought=f'Value bet: {thought_base}',
                    chat_message=_personality_chat(self._p, 'raise', locale),
                )
            if equity < _BLUFF_EQUITY_THRESH and random.random() < bluff_freq:
                # Bluff with GTO-balanced frequency
                return AIThought(
                    action='raise', amount=bet_size,
                    thought=f'Bluff: {thought_base}',
                    chat_message=_personality_chat(self._p, 'raise', locale),
                )
            return AIThought(
                action='check', amount=0,
                thought=f'Check: {thought_base}',
                chat_message=_personality_chat(self._p, 'check', locale),
            )
        else:
            # Facing a bet
            if equity >= value_threshold and equity > pot_odds + value_raise_margin:
                # Re-raise for value
                re_raise = min(int(pot * bet_fraction * 1.5), my_chips)
                re_raise = max(re_raise, min_raise)
                if re_raise <= to_call or my_chips <= to_call:
                    # Not enough chips to raise — just call
                    return AIThought(
                        action='call', amount=0,
                        thought=f'Call (value, no raise room): {thought_base}',
                        chat_message=_personality_chat(self._p, 'call', locale),
                    )
                return AIThought(
                    action='raise', amount=re_raise,
                    thought=f'Value raise: {thought_base}',
                    chat_message=_personality_chat(self._p, 'raise', locale),
                )

            if equity > pot_odds + call_margin:
                # Profitable call by equity margin
                return AIThought(
                    action='call', amount=0,
                    thought=f'Call (odds): {thought_base}',
                    chat_message=_personality_chat(self._p, 'call', locale),
                )

            if equity > pot_odds and random.random() < _MARGINAL_CALL_PROB:
                # Marginal call — mixed strategy to stay unexploitable
                return AIThought(
                    action='call', amount=0,
                    thought=f'Marginal call: {thought_base}',
                    chat_message=_personality_chat(self._p, 'call', locale),
                )

            if equity < _SEMI_BLUFF_EQUITY_THRESH and random.random() < bluff_freq * 0.5:
                # Semi-bluff raise facing a bet
                bluff_raise = min(int(pot * _WET_BET_FRAC), my_chips)
                bluff_raise = max(bluff_raise, min_raise)
                if bluff_raise > to_call and my_chips > to_call:
                    return AIThought(
                        action='raise', amount=bluff_raise,
                        thought=f'Semi-bluff raise: {thought_base}',
                        chat_message=_personality_chat(self._p, 'raise', locale),
                    )

            return AIThought(
                action='fold', amount=0,
                thought=f'Fold: {thought_base}',
                chat_message=_personality_chat(self._p, 'fold', locale),
            )

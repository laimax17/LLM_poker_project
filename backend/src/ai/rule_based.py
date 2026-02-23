"""
Rule-based poker bot strategy.
Pre-flop: uses hole-card strength heuristics.
Post-flop: uses HandEvaluator for made-hand strength.
"""
import logging
import random
from typing import Any

from ..engine import Card, Rank, Suit, HandEvaluator
from ..schemas import AIThought
from .strategy import BotStrategy

logger = logging.getLogger(__name__)

# Pre-flop chat messages keyed by action
CHAT_LINES: dict[str, list[str]] = {
    'fold':  ['I fold.', 'Not feeling it.', 'Too rich for me.'],
    'check': ['Check.', 'I\'ll check.'],
    'call':  ['I\'ll call.', 'Call.', 'Let\'s see it.'],
    'raise': ['Raise.', 'I raise.', 'Let\'s play.'],
}


def _random_chat(action: str) -> str:
    options = CHAT_LINES.get(action, ['...'])
    return random.choice(options)


class RuleBasedStrategy(BotStrategy):
    """
    Fast rule-based strategy that never calls an LLM.
    Adds ±15% noise to mimic realistic play.
    """

    def decide(self, game_state: dict[str, Any], player_id: str) -> AIThought:
        players = game_state.get('players', [])
        me = next((p for p in players if p['id'] == player_id), None)

        if not me or not me.get('is_active'):
            logger.warning('RuleBased: player %s not found or inactive, folding', player_id)
            return AIThought(action='fold', amount=0, thought='Not active', chat_message='Fold.')

        current_bet: int = game_state.get('current_bet', 0)
        my_bet: int = me.get('current_bet', 0)
        to_call: int = max(0, current_bet - my_bet)
        min_raise: int = game_state.get('min_raise', 20)
        chips: int = me.get('chips', 0)
        street: str = game_state.get('state', 'PREFLOP')

        # Parse hole cards
        hand_raw: list[dict] = me.get('hand') or []
        hand_cards: list[Card] = []
        for c in hand_raw:
            if c is not None:
                try:
                    hand_cards.append(Card(Rank(c['rank']), Suit(c['suit'])))
                except (KeyError, ValueError) as exc:
                    logger.warning('RuleBased: could not parse card %s: %s', c, exc)

        # Parse community cards
        comm_raw: list[dict] = game_state.get('community_cards', [])
        comm_cards: list[Card] = []
        for c in comm_raw:
            try:
                comm_cards.append(Card(Rank(c['rank']), Suit(c['suit'])))
            except (KeyError, ValueError) as exc:
                logger.warning('RuleBased: could not parse community card %s: %s', c, exc)

        strength = self._assess_strength(hand_cards, comm_cards, street)
        # Add ±15% noise
        strength = min(1.0, max(0.0, strength + random.uniform(-0.15, 0.15)))
        logger.debug('RuleBased: %s street=%s strength=%.2f to_call=%d', player_id, street, strength, to_call)

        return self._make_decision(strength, to_call, min_raise, chips, current_bet)

    def _assess_strength(self, hand: list[Card], community: list[Card], street: str) -> float:
        """Returns a 0.0–1.0 hand-strength estimate."""
        if street == 'PREFLOP':
            return self._preflop_strength(hand)
        all_cards = hand + community
        if len(all_cards) >= 5:
            hand_rank, _ = HandEvaluator.evaluate(all_cards)
            # HandRank enum values 1-10; normalize to 0-1
            return (hand_rank.value - 1) / 9.0
        # Not enough cards (shouldn't happen post-flop, but be safe)
        return 0.3

    def _preflop_strength(self, hand: list[Card]) -> float:
        if len(hand) < 2:
            return 0.25
        ranks = sorted([c.rank.value for c in hand], reverse=True)
        r1, r2 = ranks[0], ranks[1]
        suited = hand[0].suit == hand[1].suit

        # Premium hands
        if r1 >= 12 and r2 >= 12:   return 0.92  # QQ/KK/AA
        if r1 == 14 and r2 == 13:   return 0.85  # AKo/s
        if r1 == 14 and r2 >= 11:   return 0.75  # AQ/AJ
        if r1 >= 10 and r2 >= 10:   return 0.72  # TT-JJ
        if r1 == 9 and r2 == 9:     return 0.65  # 99
        if r1 >= 12 and suited:     return 0.60  # QJs/KTs suited
        if r1 == 14:                return 0.55  # Ax suited/offsuit
        if r1 >= 11 and r2 >= 9:   return 0.50  # KTo, QTo
        if suited and r1 >= 9:      return 0.45  # suited connectors
        return 0.25

    def _make_decision(
        self,
        strength: float,
        to_call: int,
        min_raise: int,
        chips: int,
        current_bet: int,
    ) -> AIThought:
        # Cannot call (no chips)
        if chips <= 0:
            return AIThought(action='fold', amount=0, thought='No chips', chat_message='Fold.')

        # No cost to stay in: check or bet
        if to_call == 0:
            if strength > 0.70 and chips >= min_raise:
                raise_to = current_bet + min_raise
                return AIThought(
                    action='raise', amount=raise_to,
                    thought=f'Strong hand, value-betting (str={strength:.2f})',
                    chat_message=_random_chat('raise'),
                )
            return AIThought(action='check', amount=0, thought='Checking', chat_message=_random_chat('check'))

        # Must call something
        pot_odds = to_call / (to_call + max(1, min_raise))

        if strength > pot_odds + 0.15:
            if strength > 0.75 and chips >= current_bet + min_raise:
                raise_to = current_bet + min_raise
                return AIThought(
                    action='raise', amount=raise_to,
                    thought=f'Value raise (str={strength:.2f})',
                    chat_message=_random_chat('raise'),
                )
            return AIThought(
                action='call', amount=0,
                thought=f'Good pot odds (str={strength:.2f} > odds={pot_odds:.2f})',
                chat_message=_random_chat('call'),
            )

        if strength > 0.35:
            return AIThought(
                action='call', amount=0,
                thought=f'Marginal call (str={strength:.2f})',
                chat_message=_random_chat('call'),
            )

        return AIThought(
            action='fold', amount=0,
            thought=f'Weak hand vs bet (str={strength:.2f})',
            chat_message=_random_chat('fold'),
        )

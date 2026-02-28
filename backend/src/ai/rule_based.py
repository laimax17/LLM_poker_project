"""
Rule-based poker bot strategy with personality system.
Pre-flop: uses hole-card strength heuristics.
Post-flop: uses HandEvaluator for made-hand strength.
Each bot can have a distinct personality that shifts aggression, tightness, and bluff frequency.
"""
import logging
import random
from dataclasses import dataclass
from typing import Any

from ..engine import Card, Rank, Suit, HandEvaluator
from ..schemas import AIThought
from .strategy import BotStrategy

logger = logging.getLogger(__name__)


# ─── Personality definitions ──────────────────────────────────────────────────

@dataclass(frozen=True)
class Personality:
    """Defines a bot's playing style."""
    name: str
    aggression: float   # 0.0 (passive) → 1.0 (very aggressive)
    tightness: float    # 0.0 (loose) → 1.0 (very tight)
    bluff_freq: float   # probability of bluffing when hand is weak

    # Per-personality chat lines
    chat_fold: list[str]
    chat_check: list[str]
    chat_call: list[str]
    chat_raise: list[str]


PERSONALITIES: dict[str, Personality] = {
    'shark': Personality(
        name='shark',
        aggression=0.7, tightness=0.5, bluff_freq=0.25,
        chat_fold=['Folding... for now.', 'Not worth it.', 'I\'ll wait.'],
        chat_check=['Check.', 'I\'ll let it ride.'],
        chat_call=['I call.', 'Let\'s see the next card.', 'I\'m in.'],
        chat_raise=['Raise.', 'Time to build this pot.', 'Pay up.', 'Let\'s go.'],
    ),
    'rock': Personality(
        name='rock',
        aggression=0.2, tightness=0.8, bluff_freq=0.05,
        chat_fold=['Fold.', 'Not my hand.', 'I\'ll pass.'],
        chat_check=['Check.', 'Checking.'],
        chat_call=['...call.', 'Fine, I call.', 'I\'ll see it.'],
        chat_raise=['Raise.', 'I have a hand.'],
    ),
    'maniac': Personality(
        name='maniac',
        aggression=0.9, tightness=0.15, bluff_freq=0.40,
        chat_fold=['Ugh, fine.', 'Whatever.', 'Next hand!'],
        chat_check=['Check... boring.', 'Check I guess.'],
        chat_call=['CALL!', 'Let\'s go!', 'I\'m not scared.', 'Bring it!'],
        chat_raise=['ALL DAY!', 'RAISE!', 'You scared?', 'Let\'s gamble!',
                    'Come on!', 'Can you handle this?'],
    ),
    'station': Personality(
        name='station',
        aggression=0.2, tightness=0.15, bluff_freq=0.08,
        chat_fold=['Okay... fold.', 'I guess I fold.'],
        chat_check=['Check.', 'I check.'],
        chat_call=['Call.', 'I\'ll call.', 'Let me see.', 'I call, show me.',
                   'Calling.', 'I want to see your cards.'],
        chat_raise=['Raise.', 'Small raise.'],
    ),
    'tag': Personality(
        name='tag',
        aggression=0.6, tightness=0.6, bluff_freq=0.18,
        chat_fold=['Fold.', 'Not this time.', 'I\'m out.'],
        chat_check=['Check.', 'Checking here.'],
        chat_call=['Call.', 'Good price.', 'Pot odds say call.'],
        chat_raise=['Raise.', 'Value bet.', 'I like my hand.', 'Raising.'],
    ),
}

DEFAULT_PERSONALITY = PERSONALITIES['shark']


def _chat(personality: Personality, action: str) -> str:
    """Pick a random chat line for this personality and action."""
    pool = {
        'fold':  personality.chat_fold,
        'check': personality.chat_check,
        'call':  personality.chat_call,
        'raise': personality.chat_raise,
    }
    return random.choice(pool.get(action, ['...']))


# ─── Strategy ─────────────────────────────────────────────────────────────────

class RuleBasedStrategy(BotStrategy):
    """
    Fast rule-based strategy that never calls an LLM.
    Adds noise to mimic realistic play.
    Personality traits shift aggression, tightness, and bluff frequency.
    """

    def __init__(self, personality: str = 'shark') -> None:
        self._p: Personality = PERSONALITIES.get(personality, DEFAULT_PERSONALITY)

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
        pot: int = game_state.get('pot', 0)
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
        # Add noise scaled by personality (loose players have wider variance)
        noise_range = 0.12 + (1.0 - self._p.tightness) * 0.08
        strength = min(1.0, max(0.0, strength + random.uniform(-noise_range, noise_range)))
        logger.debug(
            'RuleBased[%s]: %s street=%s strength=%.2f to_call=%d',
            self._p.name, player_id, street, strength, to_call,
        )

        return self._make_decision(strength, to_call, min_raise, chips, current_bet, pot)

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
        if r1 >= 11 and r2 >= 9:    return 0.50  # KTo, QTo
        if suited and r1 >= 9:      return 0.45  # suited connectors
        # Loose personalities see more value in marginal hands
        if r1 == r2:                return 0.42  # low pocket pairs
        if suited:                  return 0.35  # any suited
        if r1 >= 10:               return 0.32  # any broadway
        return 0.25

    def _make_decision(
        self,
        strength: float,
        to_call: int,
        min_raise: int,
        chips: int,
        current_bet: int,
        pot: int,
    ) -> AIThought:
        p = self._p

        # Personality-adjusted thresholds
        # Higher aggression → lower thresholds (bet/raise more often)
        bet_threshold = 0.70 - p.aggression * 0.18      # shark: 0.574, maniac: 0.538
        raise_threshold = 0.75 - p.aggression * 0.12     # shark: 0.666, maniac: 0.642
        # Higher aggression + lower tightness → harder to fold
        fold_threshold = 0.35 - p.aggression * 0.12 - (1.0 - p.tightness) * 0.08
        # shark: 0.226, maniac: 0.172, station: 0.172, rock: 0.306

        # Cannot call (no chips)
        if chips <= 0:
            return AIThought(action='fold', amount=0, thought='No chips',
                             chat_message=_chat(p, 'fold'))

        # ─── No bet to face: check or bet ────────────────────────────────
        if to_call == 0:
            # Value bet with strong hand
            if strength > bet_threshold and chips >= min_raise:
                raise_amount = self._size_bet(strength, pot, min_raise, chips)
                return AIThought(
                    action='raise', amount=raise_amount,
                    thought=f'[{p.name}] Value bet (str={strength:.2f})',
                    chat_message=_chat(p, 'raise'),
                )
            # Bluff with weak hand
            if strength < 0.30 and random.random() < p.bluff_freq:
                bluff_size = max(min_raise, int(pot * 0.4))
                bluff_size = min(bluff_size, chips)
                if bluff_size >= min_raise:
                    return AIThought(
                        action='raise', amount=bluff_size,
                        thought=f'[{p.name}] Bluff (str={strength:.2f})',
                        chat_message=_chat(p, 'raise'),
                    )
            return AIThought(action='check', amount=0,
                             thought=f'[{p.name}] Check (str={strength:.2f})',
                             chat_message=_chat(p, 'check'))

        # ─── Facing a bet ─────────────────────────────────────────────────
        pot_odds = to_call / (to_call + max(1, min_raise))

        # Strong hand → raise for value
        if strength > pot_odds + 0.12 and strength > raise_threshold:
            if chips >= current_bet + min_raise:
                raise_amount = self._size_bet(strength, pot, min_raise, chips)
                return AIThought(
                    action='raise', amount=raise_amount,
                    thought=f'[{p.name}] Value raise (str={strength:.2f})',
                    chat_message=_chat(p, 'raise'),
                )

        # Good odds → call
        if strength > pot_odds + 0.10:
            return AIThought(
                action='call', amount=0,
                thought=f'[{p.name}] Good odds call (str={strength:.2f} > po={pot_odds:.2f})',
                chat_message=_chat(p, 'call'),
            )

        # Marginal hand above fold threshold → call
        if strength > fold_threshold:
            return AIThought(
                action='call', amount=0,
                thought=f'[{p.name}] Marginal call (str={strength:.2f})',
                chat_message=_chat(p, 'call'),
            )

        # Weak hand but personality may bluff-raise
        if random.random() < p.bluff_freq * 0.6:
            if chips >= current_bet + min_raise:
                bluff_size = max(min_raise, int(pot * 0.55))
                bluff_size = min(bluff_size, chips)
                return AIThought(
                    action='raise', amount=bluff_size,
                    thought=f'[{p.name}] Bluff raise (str={strength:.2f})',
                    chat_message=_chat(p, 'raise'),
                )

        # Calling station special: rarely folds even when weak
        if p.tightness < 0.3 and p.aggression < 0.4 and random.random() < 0.45:
            return AIThought(
                action='call', amount=0,
                thought=f'[{p.name}] Stubborn call (str={strength:.2f})',
                chat_message=_chat(p, 'call'),
            )

        return AIThought(
            action='fold', amount=0,
            thought=f'[{p.name}] Fold (str={strength:.2f})',
            chat_message=_chat(p, 'fold'),
        )

    def _size_bet(
        self,
        strength: float,
        pot: int,
        min_raise: int,
        chips: int,
    ) -> int:
        """Pick a raise amount based on hand strength and personality."""
        p = self._p
        # Base sizing: fraction of pot scaled by strength
        if strength > 0.85:
            frac = 0.75 + p.aggression * 0.25   # big value bet
        elif strength > 0.65:
            frac = 0.45 + p.aggression * 0.20   # medium bet
        else:
            frac = 0.30 + p.aggression * 0.15   # small bet / bluff sizing

        amount = max(min_raise, int(pot * frac))
        # Add some randomness (±20%) so sizing isn't robotic
        jitter = random.uniform(0.85, 1.15)
        amount = int(amount * jitter)
        return max(min_raise, min(amount, chips))

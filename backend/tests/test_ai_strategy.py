"""
Tests for AI strategy modules.

Covers:
- RuleBasedStrategy: all 5 personalities × weak / medium / strong hand strengths
- LLMBotStrategy._parse_response: malformed JSON, invalid action, amount clamping
"""
import sys
sys.path.append('.')

import pytest

from backend.src.ai.rule_based import RuleBasedStrategy, PERSONALITIES
from backend.src.ai.llm_strategy import LLMBotStrategy
from backend.src.schemas import AIThought

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

VALID_ACTIONS = frozenset({'fold', 'check', 'call', 'raise'})

# Minimal game-state dict that RuleBasedStrategy.decide() can parse.
# 'hand' uses real card dicts so Card parsing doesn't fail.
# Ace of spades + King of spades — premium hand.
_STRONG_HAND = [
    {'rank': 14, 'suit': 'S'},  # As
    {'rank': 13, 'suit': 'S'},  # Ks
]

# 7-2 offsuit — weakest preflop hand.
_WEAK_HAND = [
    {'rank': 7, 'suit': 'S'},
    {'rank': 2, 'suit': 'H'},
]

# Medium: suited connector (8s-9s)
_MEDIUM_HAND = [
    {'rank': 8, 'suit': 'S'},
    {'rank': 9, 'suit': 'S'},
]


def _make_state(
    hand: list,
    *,
    street: str = 'PREFLOP',
    pot: int = 100,
    current_bet: int = 0,
    min_raise: int = 20,
    player_chips: int = 1000,
    player_current_bet: int = 0,
    community_cards: list | None = None,
) -> dict:
    """Build a minimal game-state dict for the given player."""
    return {
        'state': street,
        'pot': pot,
        'current_bet': current_bet,
        'min_raise': min_raise,
        'community_cards': community_cards or [],
        'players': [
            {
                'id': 'bot_1',
                'name': 'TEST',
                'chips': player_chips,
                'hand': hand,
                'is_active': True,
                'current_bet': player_current_bet,
                'is_all_in': False,
                'has_acted': False,
                'is_dealer': True,
            }
        ],
    }


# ---------------------------------------------------------------------------
# RuleBasedStrategy — action validity for all personalities
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('personality', list(PERSONALITIES.keys()))
@pytest.mark.parametrize('hand,label', [
    (_STRONG_HAND, 'strong'),
    (_MEDIUM_HAND, 'medium'),
    (_WEAK_HAND, 'weak'),
])
def test_rule_based_returns_valid_action(personality: str, hand: list, label: str) -> None:
    """Every personality × hand-strength combination must return a valid action."""
    strategy = RuleBasedStrategy(personality=personality)
    state = _make_state(hand)
    result = strategy.decide(state, 'bot_1')

    assert isinstance(result, AIThought), f'{personality}/{label}: expected AIThought'
    assert result.action in VALID_ACTIONS, (
        f'{personality}/{label}: got unexpected action {result.action!r}'
    )
    assert isinstance(result.amount, int), f'{personality}/{label}: amount must be int'
    assert result.amount >= 0, f'{personality}/{label}: amount must be non-negative'


@pytest.mark.parametrize('personality', list(PERSONALITIES.keys()))
def test_rule_based_no_chips_folds(personality: str) -> None:
    """A player with 0 chips always folds (can't bet)."""
    strategy = RuleBasedStrategy(personality=personality)
    state = _make_state(_STRONG_HAND, player_chips=0)
    result = strategy.decide(state, 'bot_1')
    assert result.action == 'fold', f'{personality}: expected fold with 0 chips, got {result.action}'


def test_rule_based_postflop_valid_action() -> None:
    """Post-flop (FLOP state) must also return a valid action."""
    community = [
        {'rank': 2, 'suit': 'H'},
        {'rank': 7, 'suit': 'D'},
        {'rank': 11, 'suit': 'S'},
    ]
    strategy = RuleBasedStrategy(personality='shark')
    state = _make_state(
        _STRONG_HAND,
        street='FLOP',
        community_cards=community,
        current_bet=40,
        player_current_bet=0,
    )
    result = strategy.decide(state, 'bot_1')
    assert result.action in VALID_ACTIONS


def test_rule_based_facing_bet_valid_action() -> None:
    """When facing a bet that exceeds chips, bot should still produce a valid action."""
    strategy = RuleBasedStrategy(personality='rock')
    state = _make_state(
        _WEAK_HAND,
        current_bet=500,        # large bet
        player_chips=200,       # less than required to call fully
        player_current_bet=0,
    )
    result = strategy.decide(state, 'bot_1')
    assert result.action in VALID_ACTIONS


# ---------------------------------------------------------------------------
# LLMBotStrategy._parse_response — unit tests (no LLM call needed)
# ---------------------------------------------------------------------------

class _FakeLLMClient:
    """Stub that satisfies LLMBotStrategy's type requirement."""
    async def chat(self, system: str, user: str) -> str:  # pragma: no cover
        return ''

    async def health_check(self) -> bool:  # pragma: no cover
        return True


def _make_llm_strategy() -> LLMBotStrategy:
    return LLMBotStrategy(_FakeLLMClient())  # type: ignore[arg-type]


def _base_game_state(player_chips: int = 1000, current_bet: int = 0, min_raise: int = 20) -> dict:
    return {
        'state': 'FLOP',
        'pot': 100,
        'current_bet': current_bet,
        'min_raise': min_raise,
        'community_cards': [],
        'players': [
            {
                'id': 'bot_1',
                'chips': player_chips,
                'current_bet': 0,
                'hand': [],
                'is_active': True,
                'is_all_in': False,
                'has_acted': False,
            }
        ],
    }


def test_parse_response_valid_call() -> None:
    """Well-formed JSON with 'call' action parses correctly."""
    llm = _make_llm_strategy()
    raw = '{"action": "call", "amount": 0, "thought": "good odds", "chat_message": "I call."}'
    result = llm._parse_response(raw, _base_game_state())
    assert result.action == 'call'
    assert result.amount == 0
    assert result.thought == 'good odds'


def test_parse_response_valid_raise() -> None:
    """Well-formed JSON with 'raise' action and valid amount passes through."""
    llm = _make_llm_strategy()
    # current_bet=0, min_raise=20 → min raise = 20; player has 1000 chips
    raw = '{"action": "raise", "amount": 60, "thought": "value", "chat_message": "Raise."}'
    result = llm._parse_response(raw, _base_game_state(), player_id='bot_1')
    assert result.action == 'raise'
    assert result.amount == 60


def test_parse_response_raise_clamped_to_min() -> None:
    """Raise amount below the minimum is bumped up to the minimum."""
    llm = _make_llm_strategy()
    # current_bet=100, min_raise=20 → min total = 120
    raw = '{"action": "raise", "amount": 50, "thought": "", "chat_message": ""}'
    result = llm._parse_response(
        raw,
        _base_game_state(current_bet=100, min_raise=20),
        player_id='bot_1',
    )
    assert result.action == 'raise'
    assert result.amount >= 120


def test_parse_response_raise_clamped_to_chips() -> None:
    """Raise amount above player's total chips is clamped down."""
    llm = _make_llm_strategy()
    # player_chips=200, current_bet=0, min_raise=20 → max total = 200
    raw = '{"action": "raise", "amount": 9999, "thought": "", "chat_message": ""}'
    result = llm._parse_response(
        raw,
        _base_game_state(player_chips=200, current_bet=0, min_raise=20),
        player_id='bot_1',
    )
    assert result.action == 'raise'
    assert result.amount <= 200


def test_parse_response_invalid_action_defaults_to_fold() -> None:
    """An unrecognised action string in LLM output falls back to 'fold'."""
    llm = _make_llm_strategy()
    raw = '{"action": "allin", "amount": 0, "thought": "yolo", "chat_message": "all in!"}'
    result = llm._parse_response(raw, _base_game_state())
    assert result.action == 'fold'


def test_parse_response_no_json_raises() -> None:
    """LLM output without any JSON object raises ValueError."""
    llm = _make_llm_strategy()
    with pytest.raises(ValueError, match='No JSON found'):
        llm._parse_response('Sorry, I cannot decide.', _base_game_state())


def test_parse_response_malformed_json_raises() -> None:
    """LLM output with broken JSON raises ValueError."""
    llm = _make_llm_strategy()
    with pytest.raises(ValueError):
        llm._parse_response('{action: fold broken json!!!}', _base_game_state())


def test_parse_response_json_embedded_in_text() -> None:
    """JSON buried inside prose text is extracted correctly."""
    llm = _make_llm_strategy()
    raw = (
        'Let me think... After careful analysis, I decide: '
        '{"action": "check", "amount": 0, "thought": "pot control", "chat_message": "Check."} '
        'This is the best play here.'
    )
    result = llm._parse_response(raw, _base_game_state())
    assert result.action == 'check'


def test_parse_response_missing_fields_use_defaults() -> None:
    """Partial JSON (missing optional fields) does not crash; defaults are used."""
    llm = _make_llm_strategy()
    raw = '{"action": "fold"}'
    result = llm._parse_response(raw, _base_game_state())
    assert result.action == 'fold'
    assert result.amount == 0
    assert result.thought == ''
    assert result.chat_message == ''

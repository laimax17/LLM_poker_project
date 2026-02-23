"""
LLM-powered bot strategy.
Pre-flop: always delegates to RuleBasedStrategy (for speed).
Post-flop (Flop/Turn/River): calls the LLM for a decision.
Falls back to RuleBasedStrategy on any error.
"""
import json
import logging
import re
from typing import Any

from ..schemas import AIThought
from .llm_client import LLMClient
from .rule_based import RuleBasedStrategy
from .strategy import BotStrategy

logger = logging.getLogger(__name__)

BOT_SYSTEM_PROMPT = (
    '你是一个德州扑克 AI 玩家。你的风格是：理性、数学导向、偶尔诈唬。\n'
    '你必须严格按照以下 JSON 格式返回决策，不要包含任何其他内容：\n'
    '{"action": "fold|call|raise|check", "amount": 0, "thought": "简短推理", "chat_message": "对其他玩家说的话"}\n'
    'amount 仅在 action 为 raise 时有意义。'
)

JSON_RE = re.compile(r'\{[^{}]*\}', re.DOTALL)

VALID_ACTIONS = frozenset({'fold', 'check', 'call', 'raise'})


class LLMBotStrategy(BotStrategy):
    """
    Hybrid strategy: rule-based pre-flop, LLM post-flop.
    Requires decide_async() for post-flop; decide() is synchronous (pre-flop only).
    """

    def __init__(self, llm_client: LLMClient) -> None:
        self.llm = llm_client
        self._rule_based = RuleBasedStrategy()

    def decide(self, game_state: dict[str, Any], player_id: str) -> AIThought:
        """Synchronous decide — always uses rule-based (for pre-flop calls)."""
        return self._rule_based.decide(game_state, player_id)

    async def decide_async(self, game_state: dict[str, Any], player_id: str) -> AIThought:
        """
        Async decide:
        - PREFLOP → rule-based immediately
        - FLOP/TURN/RIVER → LLM with rule-based fallback
        """
        street: str = game_state.get('state', 'PREFLOP')

        if street == 'PREFLOP':
            return self._rule_based.decide(game_state, player_id)

        try:
            user_prompt = self._build_prompt(game_state, player_id)
            raw = await self.llm.chat(BOT_SYSTEM_PROMPT, user_prompt)
            decision = self._parse_response(raw, game_state)
            logger.debug('LLMBotStrategy decision for %s: %s', player_id, decision.action)
            return decision
        except Exception as exc:
            logger.warning(
                'LLMBotStrategy LLM call failed for %s (falling back to rule-based): %s',
                player_id, exc,
            )
            return self._rule_based.decide(game_state, player_id)

    def _build_prompt(self, game_state: dict[str, Any], player_id: str) -> str:
        players = game_state.get('players', [])
        me = next((p for p in players if p['id'] == player_id), {})
        to_call = max(0, game_state.get('current_bet', 0) - me.get('current_bet', 0))
        return (
            f"当前局面：\n"
            f"- 街道: {game_state.get('state')}\n"
            f"- 我的手牌: {me.get('hand')}\n"
            f"- 公共牌: {game_state.get('community_cards')}\n"
            f"- 底池: {game_state.get('pot')}\n"
            f"- 需要跟注: {to_call}\n"
            f"- 我的筹码: {me.get('chips')}\n"
            f"- 最小加注: {game_state.get('min_raise')}\n"
            f"请给出你的决策。"
        )

    def _parse_response(self, raw: str, game_state: dict[str, Any]) -> AIThought:
        match = JSON_RE.search(raw)
        if not match:
            raise ValueError(f'No JSON found in LLM response: {raw[:200]!r}')

        try:
            data = json.loads(match.group())
        except json.JSONDecodeError as exc:
            raise ValueError(f'JSON decode error: {exc}') from exc

        action = str(data.get('action', 'fold')).lower()
        if action not in VALID_ACTIONS:
            logger.warning('LLM returned invalid action %r, defaulting to fold', action)
            action = 'fold'

        amount = int(data.get('amount', 0))
        # Clamp raise amount
        if action == 'raise':
            min_raise = game_state.get('current_bet', 0) + game_state.get('min_raise', 20)
            amount = max(min_raise, amount)

        return AIThought(
            action=action,
            amount=amount,
            thought=str(data.get('thought', '')),
            chat_message=str(data.get('chat_message', '')),
        )

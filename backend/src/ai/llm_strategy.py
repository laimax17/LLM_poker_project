"""
LLM-powered bot strategy (agentic).

Pre-flop: delegates to RuleBasedStrategy (fast, range-table driven).
Post-flop: builds an *enriched* prompt — pre-computed equity, pot odds,
position, board texture and opponent reads — and asks the model for a single
+EV decision. Falls back to RuleBasedStrategy on any error.

The model reasons over numbers we computed for it (see analytics.py) instead
of guessing them, and is given opponent profiles (see opponent_model.py) so it
can exploit tendencies — that combination is what makes the bot "agentic".
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Optional

from ..schemas import AIThought
from .analytics import compute_analytics
from .llm_client import LLMClient
from .rule_based import RuleBasedStrategy
from .strategy import BotStrategy

logger = logging.getLogger(__name__)

BOT_SYSTEM_PROMPT = (
    '你是一名职业德州扑克 AI 玩家，理性、数学导向、懂得利用对手漏洞，偶尔诈唬。\n'
    '你会收到已经替你算好的关键数据（胜率、底池赔率、位置、牌面质地、对手画像）。\n'
    '请基于这些数据做出 +EV 的决策：胜率远超底池赔率时为价值下注/加注；'
    '胜率不足且无听牌时考虑弃牌；面对偏紧(rock/TAG)的对手可多诈唬，'
    '面对跟注站(station)则减少诈唬、加大价值下注。\n'
    '严格只返回如下 JSON，不要任何额外文字：\n'
    '{"action": "fold|call|raise|check", "amount": 0, "thought": "简短推理", "chat_message": "对其他玩家说的话"}\n'
    'amount 仅在 action 为 raise 时有意义，且必须在最小加注与你的筹码之间。'
)

JSON_RE = re.compile(r'\{[^{}]*\}', re.DOTALL)
VALID_ACTIONS = frozenset({'fold', 'check', 'call', 'raise'})


class LLMBotStrategy(BotStrategy):
    """Hybrid agent: rule-based pre-flop, enriched-prompt LLM post-flop."""

    def __init__(self, llm_client: LLMClient) -> None:
        self.llm = llm_client
        self._rule_based = RuleBasedStrategy()

    def decide(self, game_state: dict[str, Any], player_id: str) -> AIThought:
        """Synchronous decide — always rule-based (used for pre-flop calls)."""
        return self._rule_based.decide(game_state, player_id)

    async def decide_async(
        self,
        game_state: dict[str, Any],
        player_id: str,
        opponents: Optional[dict[str, dict[str, Any]]] = None,
    ) -> AIThought:
        """PREFLOP → rule-based; post-flop → enriched-prompt LLM (with fallback)."""
        street: str = game_state.get('state', 'PREFLOP')
        if street == 'PREFLOP':
            return self._rule_based.decide(game_state, player_id)

        try:
            user_prompt = self._build_prompt(game_state, player_id, opponents or {})
            raw = await self.llm.chat(BOT_SYSTEM_PROMPT, user_prompt)
            decision = self._parse_response(raw, game_state, player_id)
            logger.debug('LLMBotStrategy decision for %s: %s', player_id, decision.action)
            return decision
        except Exception as exc:
            logger.warning(
                'LLMBotStrategy LLM call failed for %s (falling back to rule-based): %s',
                player_id, exc,
            )
            return self._rule_based.decide(game_state, player_id)

    def _build_prompt(
        self,
        game_state: dict[str, Any],
        player_id: str,
        opponents: dict[str, dict[str, Any]],
    ) -> str:
        a = compute_analytics(game_state, player_id)
        if not a:
            # Analytics unavailable — fall back to a minimal prompt.
            return '请根据当前德州扑克局面给出决策。'

        equity = a.get('equity')
        equity_line = f"{equity:.0%}" if equity is not None else '未知'
        draws = '、'.join(a.get('board_draws', [])) or '干燥'

        # Opponent reads
        if opponents:
            opp_lines = '\n'.join(
                f"  - {pid}: {prof.get('label')}"
                + (
                    f" (VPIP {prof['vpip']:.0%}/PFR {prof['pfr']:.0%}/AF {prof['af']}, {prof['hands']}手)"
                    if 'vpip' in prof else f" ({prof.get('hands', 0)}手, 样本不足)"
                )
                for pid, prof in opponents.items()
            )
        else:
            opp_lines = '  - 暂无对手数据'

        return (
            f"当前局面：\n"
            f"- 街道: {a['street']}\n"
            f"- 我的位置: {a['position_label']}\n"
            f"- 我的手牌: {a['hand_str']}\n"
            f"- 公共牌: {a['board_str']}（{draws}，湿润度 {a.get('board_wetness', 0):.0%}）\n"
            f"- 我的胜率估计: {equity_line}（对 {a['active_opponents']} 名活跃对手）\n"
            f"- 底池: {a['pot']}，需要跟注: {a['to_call']}，底池赔率: {a['pot_odds']:.0%}\n"
            f"- 我的筹码: {a['my_chips']}，最小加注: {a['min_raise']}，本街加注次数: {a['raise_count']}\n"
            f"- 对手画像:\n{opp_lines}\n"
            f"请综合以上数据给出你的决策（JSON）。"
        )

    def _parse_response(
        self, raw: str, game_state: dict[str, Any], player_id: str = ''
    ) -> AIThought:
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
        if action == 'raise':
            players = game_state.get('players', [])
            me = next((p for p in players if p.get('id') == player_id), {})
            my_total = me.get('chips', 0) + me.get('current_bet', 0)
            min_raise = game_state.get('current_bet', 0) + game_state.get('min_raise', 20)
            amount = max(min_raise, min(amount, my_total) if my_total > 0 else amount)

        return AIThought(
            action=action,
            amount=amount,
            thought=str(data.get('thought', '')),
            chat_message=str(data.get('chat_message', '')),
        )

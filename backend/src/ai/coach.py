"""
AI Coach for the human player.
Returns teaching-style Chinese analysis of the current hand.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from .analytics import compute_analytics
from .llm_client import LLMClient

logger = logging.getLogger(__name__)


def _extract_json(text: str) -> str | None:
    """Extract the first complete JSON object from text using bracket counting.

    More robust than a greedy regex: correctly handles nested objects/arrays
    and ignores any trailing explanation text the LLM may append.
    """
    start = text.find('{')
    if start == -1:
        return None
    depth = 0
    for i, ch in enumerate(text[start:], start):
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    return None


COACH_SYSTEM_PROMPT = (
    '你是一个专业的德州扑克教练，用中文进行教学分析。\n'
    '在提到具体牌时，使用"rank+花色符号"格式，例如"A♠"、"K♥"、"Q♦"。\n'
    '你的回答必须是以下 JSON 格式（不要包含任何其他内容）：\n'
    '{\n'
    '  "recommendation": "FOLD|CALL|CHECK|RAISE",\n'
    '  "recommended_amount": 0,\n'
    '  "body": "教学分析，200-400字，包含底池赔率、位置分析、对手范围推断，用A♠这样的格式引用牌",\n'
    '  "stats": [\n'
    '    {"label": "底池赔率", "value": "24%", "quality": "bad"},\n'
    '    {"label": "胜率估计", "value": "42%", "quality": "neutral"},\n'
    '    {"label": "位置", "value": "IP ✓", "quality": "good"},\n'
    '    {"label": "推荐", "value": "RAISE", "quality": "hot"}\n'
    '  ]\n'
    '}\n'
    'quality 只能是: good, bad, hot, neutral'
)

VALID_RECS = frozenset({'FOLD', 'CALL', 'CHECK', 'RAISE'})
VALID_QUALITIES = frozenset({'good', 'bad', 'hot', 'neutral'})


class AICoach:
    """Analyzes the current game state for the human player."""

    def __init__(self, llm_client: LLMClient) -> None:
        self.llm = llm_client

    async def analyze(self, game_state: dict[str, Any], player_id: str) -> dict[str, Any]:
        """
        Returns a dict matching the AICoachAdvice TypeScript interface:
        { recommendation, recommendedAmount, body, stats }
        """
        user_prompt = self._build_prompt(game_state, player_id)
        try:
            raw = await self.llm.chat(COACH_SYSTEM_PROMPT, user_prompt)
            return self._parse_response(raw)
        except Exception as exc:
            logger.error('AICoach analyze failed: %s', exc)
            return self._fallback()

    def _build_prompt(self, game_state: dict[str, Any], player_id: str) -> str:
        # Ground the LLM in pre-computed numbers (equity / pot odds / position /
        # board texture / GTO range freq) so its analysis is accurate, not guessed.
        a = compute_analytics(game_state, player_id)
        if not a:
            return '请根据当前德州扑克局面提供教学分析。'

        lines = [
            f"当前街道: {a['street']}",
            f"我的位置: {a['position_label']}",
            f"我的手牌: {a['hand_str']}（请用 A♠ 这样的花色符号格式引用）",
            f"公共牌: {a['board_str']}",
            f"底池: ${a['pot']}，需要跟注: ${a['to_call']}，底池赔率: {a['pot_odds']:.0%}",
            f"最小加注: ${a['min_raise']}，我的筹码: ${a['my_chips']}",
            f"活跃对手数: {a['active_opponents']}",
        ]
        if a['street'] == 'PREFLOP':
            lines.append(
                f"GTO 参考：{a.get('combo', '')} 在 {a['position']} 开池频率 "
                f"{a.get('open_freq', 0):.0%}，跟注频率 {a.get('call_freq', 0):.0%}"
            )
        else:
            draws = '、'.join(a.get('board_draws', [])) or '干燥'
            lines.append(
                f"胜率估计: {a.get('equity', 0):.0%}（蒙特卡洛），"
                f"牌面: {draws}（湿润度 {a.get('board_wetness', 0):.0%}）"
            )
        lines.append('请基于以上数据提供详细的教学分析：')
        return '\n'.join(lines)

    def _parse_response(self, raw: str) -> dict[str, Any]:
        json_str = _extract_json(raw)
        if not json_str:
            logger.warning('AICoach: no JSON in response, using fallback')
            return self._fallback()

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as exc:
            logger.warning('AICoach: JSON decode error %s, using fallback', exc)
            return self._fallback()

        recommendation = str(data.get('recommendation', 'CHECK')).upper()
        if recommendation not in VALID_RECS:
            recommendation = 'CHECK'

        # Validate stats
        raw_stats = data.get('stats', [])
        stats: list[dict[str, str]] = []
        for s in raw_stats:
            quality = s.get('quality', 'neutral')
            if quality not in VALID_QUALITIES:
                quality = 'neutral'
            stats.append({
                'label': str(s.get('label', '')),
                'value': str(s.get('value', '')),
                'quality': quality,
            })

        return {
            'recommendation': recommendation,
            'recommendedAmount': data.get('recommended_amount'),
            'body': str(data.get('body', '')),
            'stats': stats,
        }

    def _fallback(self) -> dict[str, Any]:
        return {
            'recommendation': 'CHECK',
            'recommendedAmount': None,
            'body': 'AI Coach 暂时不可用，请检查 LLM 配置。',
            'stats': [
                {'label': '状态', 'value': 'OFFLINE', 'quality': 'bad'},
            ],
        }

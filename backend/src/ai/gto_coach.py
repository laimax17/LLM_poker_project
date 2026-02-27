"""
GTO Coach for the human player — no LLM required.

Provides position-based pre-flop analysis and Monte Carlo equity-based
post-flop advice. Returns the same dict schema as AICoach so the frontend
needs no changes.
"""
from __future__ import annotations

import logging
from typing import Any, List, Optional

from ..engine import Card, Rank, Suit
from .preflop_ranges import (
    get_hand_combo,
    get_position,
    preflop_open_freq,
    preflop_call_freq,
)
from .equity import estimate_equity
from .board_texture import analyze_board

logger = logging.getLogger(__name__)

# ─── Card parsing (same helper as in gto_strategy) ───────────────────────────

def _dict_to_card(d: Optional[dict[str, Any]]) -> Optional[Card]:
    if d is None:
        return None
    try:
        rank = Rank(int(d['rank']))
        suit = Suit(str(d['suit']))
        return Card(rank=rank, suit=suit)
    except (KeyError, ValueError):
        return None


def _parse_hand(hand_raw: List[Optional[dict[str, Any]]]) -> List[Card]:
    result: List[Card] = []
    for d in hand_raw:
        card = _dict_to_card(d)
        if card is not None:
            result.append(card)
    return result


# ─── Rank / suit display helpers ─────────────────────────────────────────────

_RANK_CHAR = {
    14: 'A', 13: 'K', 12: 'Q', 11: 'J', 10: 'T',
    9: '9', 8: '8', 7: '7', 6: '6', 5: '5', 4: '4', 3: '3', 2: '2',
}
_SUIT_CHAR = {
    'Hearts': '♥', 'Diamonds': '♦', 'Clubs': '♣', 'Spades': '♠',
}


def _card_str(card: Card) -> str:
    r = _RANK_CHAR.get(card.rank.value, str(card.rank.value))
    s = _SUIT_CHAR.get(card.suit.value, card.suit.value[0])
    return r + s


def _quality(value: float, good_threshold: float, bad_threshold: float) -> str:
    """Map a numeric value to a quality label."""
    if value >= good_threshold:
        return 'good'
    if value <= bad_threshold:
        return 'bad'
    return 'neutral'


# ─── GTO Coach ────────────────────────────────────────────────────────────────

class GTOCoach:
    """
    GTO-based coaching analysis — works without any LLM.

    Interface is identical to AICoach.analyze() so main.py needs no changes:
        async def analyze(game_state, player_id) -> dict[str, Any]
    """

    # Number of simulations for equity estimation
    N_SIM: int = 500

    async def analyze(self, game_state: dict[str, Any], player_id: str) -> dict[str, Any]:
        """
        Analyze the current game state for the human player.

        Returns a dict matching the AICoachAdvice TypeScript interface:
            { recommendation, recommendedAmount, body, stats }
        """
        try:
            return self._analyze_sync(game_state, player_id)
        except Exception as exc:
            logger.error('GTOCoach.analyze error: %s', exc)
            return self._fallback()

    def _analyze_sync(self, game_state: dict[str, Any], player_id: str) -> dict[str, Any]:
        players: List[dict[str, Any]] = game_state.get('players', [])
        me = next((p for p in players if p['id'] == player_id), None)
        if me is None:
            return self._fallback()

        street: str = game_state.get('state', 'PREFLOP')
        pot: int = game_state.get('pot', 0)
        current_bet: int = game_state.get('current_bet', 0)
        min_raise: int = game_state.get('min_raise', 20)
        my_bet: int = me.get('current_bet', 0)
        my_chips: int = me.get('chips', 0)
        to_call: int = max(0, current_bet - my_bet)
        can_check: bool = to_call == 0

        my_hand = _parse_hand(me.get('hand', []))
        community_raw: List[Any] = game_state.get('community_cards', [])
        community = _parse_hand(community_raw)

        opponents = [p for p in players if p['id'] != player_id]
        active_opponents = sum(1 for p in opponents if p.get('is_active'))

        # Position
        dealer_idx = next(
            (i for i, p in enumerate(players) if p.get('is_dealer')), 0
        )
        my_idx = next((i for i, p in enumerate(players) if p['id'] == player_id), 0)
        position = get_position(my_idx, dealer_idx, len(players))
        position_label = _position_display(position)

        hand_str = ' '.join(_card_str(c) for c in my_hand) if my_hand else '??'
        board_str = ' '.join(_card_str(c) for c in community) if community else '（等待翻牌）'

        if street == 'PREFLOP':
            return self._analyze_preflop(
                my_hand=my_hand,
                hand_str=hand_str,
                position=position,
                position_label=position_label,
                to_call=to_call,
                can_check=can_check,
                pot=pot,
                min_raise=min_raise,
                my_chips=my_chips,
                active_opponents=active_opponents,
            )
        else:
            return self._analyze_postflop(
                my_hand=my_hand,
                hand_str=hand_str,
                community=community,
                board_str=board_str,
                street=street,
                position=position,
                position_label=position_label,
                to_call=to_call,
                can_check=can_check,
                pot=pot,
                min_raise=min_raise,
                my_chips=my_chips,
                active_opponents=active_opponents,
            )

    # ── Pre-flop analysis ─────────────────────────────────────────────────────

    def _analyze_preflop(
        self,
        my_hand: List[Card],
        hand_str: str,
        position: str,
        position_label: str,
        to_call: int,
        can_check: bool,
        pot: int,
        min_raise: int,
        my_chips: int,
        active_opponents: int,
    ) -> dict[str, Any]:
        if len(my_hand) < 2:
            return self._fallback()

        combo = get_hand_combo(my_hand[0], my_hand[1])
        open_f = preflop_open_freq(combo, position)
        call_f = preflop_call_freq(combo, position)

        if can_check:
            freq = open_f
            if freq >= 0.8:
                rec = 'RAISE'
                rec_amount = min(int(min_raise * 2.5), my_chips)
                strength_label = '强'
                action_desc = f'这是一手在 {position_label} 的强起手牌（开注频率 {freq:.0%}），标准开注尺度为 2.5×BB。'
            elif freq >= 0.5:
                rec = 'RAISE'
                rec_amount = min(int(min_raise * 2.5), my_chips)
                strength_label = '中等偏强'
                action_desc = f'在 {position_label} 此手牌属于中等偏强范围（开注频率 {freq:.0%}），可以开注。'
            elif freq >= 0.2:
                rec = 'CHECK'
                rec_amount = None
                strength_label = '边缘'
                action_desc = f'在 {position_label} 此手牌属于边缘范围（开注频率 {freq:.0%}），可以用混频策略开注或 check。'
            else:
                rec = 'FOLD'
                rec_amount = None
                strength_label = '弱'
                action_desc = f'在 {position_label} 此手牌范围外（GTO 开注频率 {freq:.0%}），建议弃牌。'
        else:
            # Facing a raise
            freq = call_f
            pot_odds = to_call / (pot + to_call + 1e-6)
            if freq >= 0.75:
                rec = 'CALL'
                rec_amount = None
                strength_label = '强'
                action_desc = f'面对加注，{combo} 在 {position_label} 的跟注频率为 {freq:.0%}，满足底池赔率要求（{pot_odds:.0%}），建议跟注。'
            elif freq >= 0.4:
                rec = 'CALL'
                rec_amount = None
                strength_label = '可跟注'
                action_desc = f'面对加注，{combo} 在 {position_label} 跟注频率 {freq:.0%}，属于混频跟注范围。'
            else:
                rec = 'FOLD'
                rec_amount = None
                strength_label = '范围外'
                action_desc = f'面对加注，{combo} 在 {position_label} 超出跟注范围（频率 {freq:.0%}），建议弃牌。'

        # Stats
        rec_quality = 'hot' if rec == 'RAISE' else ('good' if rec == 'CALL' else 'bad')
        pos_quality = _pos_quality(position)

        body = (
            f'【翻牌前分析】手牌：{hand_str}，位置：{position_label}\n\n'
            f'{action_desc}\n\n'
            f'GTO 要点：\n'
            f'• 开注范围：{position_label} GTO 开注约 {_approx_open_pct(position)}% 的手牌\n'
            f'• {combo} 属于{strength_label}手牌，开注频率 {open_f:.0%}\n'
            f'• 翻牌前混频策略避免对手锁定你的范围\n'
            f'• 注意位置优势：BTN > CO > MP > EP'
        )

        stats = [
            {'label': '手牌强度', 'value': strength_label, 'quality': _quality(open_f, 0.7, 0.3)},
            {'label': '开注频率', 'value': f'{open_f:.0%}', 'quality': _quality(open_f, 0.6, 0.25)},
            {'label': '位置', 'value': position_label, 'quality': pos_quality},
            {'label': '推荐', 'value': rec, 'quality': rec_quality},
        ]

        return {
            'recommendation': rec,
            'recommendedAmount': rec_amount,
            'body': body,
            'stats': stats,
        }

    # ── Post-flop analysis ────────────────────────────────────────────────────

    def _analyze_postflop(
        self,
        my_hand: List[Card],
        hand_str: str,
        community: List[Card],
        board_str: str,
        street: str,
        position: str,
        position_label: str,
        to_call: int,
        can_check: bool,
        pot: int,
        min_raise: int,
        my_chips: int,
        active_opponents: int,
    ) -> dict[str, Any]:
        num_opp = max(1, active_opponents)
        equity = estimate_equity(my_hand, community, num_opp, n_sim=self.N_SIM)
        texture = analyze_board(community)

        pot_odds = to_call / (pot + to_call + 1e-6) if to_call > 0 else 0.0

        # Bet size for recommendation
        if texture.wetness >= 0.5:
            bet_fraction = 0.66
            value_threshold = 0.70
        else:
            bet_fraction = 0.33
            value_threshold = 0.65
        bet_size = max(int(pot * bet_fraction), min_raise)
        bet_size = min(bet_size, my_chips)

        bluff_freq = bet_size / (pot + 2 * bet_size + 1e-6)

        # Recommendation
        if can_check:
            if equity >= value_threshold:
                rec = 'RAISE'
                rec_amount = bet_size
                rec_reason = f'胜率 {equity:.0%} 超过价值下注阈值（{value_threshold:.0%}），建议下注 {int(bet_fraction * 100)}% 底池获取价值。'
            elif equity >= 0.45:
                rec = 'CHECK'
                rec_amount = None
                rec_reason = f'胜率 {equity:.0%} 属中等，建议 check 进行底池控制，避免膨胀底池。'
            else:
                rec = 'CHECK'
                rec_amount = None
                rec_reason = f'胜率 {equity:.0%} 较低，建议 check。如果对手下注可以考虑弃牌（GTO 诈唬频率 {bluff_freq:.0%}）。'
        else:
            if equity > pot_odds + 0.12:
                rec = 'CALL'
                rec_amount = None
                rec_reason = f'胜率 {equity:.0%} 远超底池赔率 {pot_odds:.0%}，建议跟注，有充分的权益优势。'
            elif equity > pot_odds + 0.05:
                rec = 'CALL'
                rec_amount = None
                rec_reason = f'胜率 {equity:.0%} 略高于底池赔率 {pot_odds:.0%}，属于临界跟注，建议跟注。'
            else:
                rec = 'FOLD'
                rec_amount = None
                rec_reason = f'胜率 {equity:.0%} 不满足底池赔率要求 {pot_odds:.0%}，建议弃牌。'

        # Board texture description
        texture_parts = []
        if texture.flush_draw:
            texture_parts.append('同花听牌')
        if texture.straight_draw:
            texture_parts.append('顺子听牌')
        if texture.paired:
            texture_parts.append('对子牌面')
        texture_desc = '、'.join(texture_parts) if texture_parts else '干燥牌面'
        wetness_label = '湿润' if texture.wetness >= 0.5 else '干燥'

        street_cn = {'FLOP': '翻牌', 'TURN': '转牌', 'RIVER': '河牌'}.get(street, street)

        body = (
            f'【{street_cn}分析】手牌：{hand_str}，公共牌：{board_str}\n\n'
            f'{rec_reason}\n\n'
            f'GTO 要点：\n'
            f'• 胜率：{equity:.0%}，底池赔率：{pot_odds:.0%}（需要满足才能盈利跟注）\n'
            f'• 牌面质地：{texture_desc}（{wetness_label}，湿润度 {texture.wetness:.0%}）\n'
            f'• 建议下注尺度：{int(bet_fraction * 100)}% 底池（约 ${bet_size}）\n'
            f'• GTO 诈唬比例：{bluff_freq:.0%}，保持价值/诈唬平衡\n'
            f'• 位置：{position_label}，{"有位置优势" if _is_ip(position) else "位置劣势，注意保守"}'
        )

        rec_quality = 'hot' if rec == 'RAISE' else ('good' if rec == 'CALL' else 'bad')
        pos_quality = _pos_quality(position)
        odds_quality = _quality(equity - pot_odds, 0.1, -0.05)

        stats = [
            {'label': '胜率估计', 'value': f'{equity:.0%}', 'quality': _quality(equity, 0.65, 0.40)},
            {'label': '底池赔率', 'value': f'{pot_odds:.0%}', 'quality': odds_quality},
            {'label': '位置', 'value': position_label + (' ✓' if _is_ip(position) else ' ✗'), 'quality': pos_quality},
            {'label': '推荐', 'value': rec, 'quality': rec_quality},
        ]

        return {
            'recommendation': rec,
            'recommendedAmount': rec_amount,
            'body': body,
            'stats': stats,
        }

    def _fallback(self) -> dict[str, Any]:
        return {
            'recommendation': 'CHECK',
            'recommendedAmount': None,
            'body': 'GTO Coach 暂时无法分析当前局面，请稍后再试。',
            'stats': [
                {'label': '状态', 'value': 'ERROR', 'quality': 'bad'},
            ],
        }


# ─── Position helpers ─────────────────────────────────────────────────────────

def _position_display(pos: str) -> str:
    mapping = {
        'BTN': 'BTN（按钮位）',
        'CO': 'CO（截止位）',
        'MP': 'MP（中间位）',
        'EP': 'EP（早期位）',
        'SB': 'SB（小盲）',
        'BB': 'BB（大盲）',
    }
    return mapping.get(pos, pos)


def _is_ip(pos: str) -> bool:
    """Return True if the position has positional advantage (acts last post-flop)."""
    return pos in ('BTN', 'CO')


def _pos_quality(pos: str) -> str:
    if pos in ('BTN', 'CO'):
        return 'good'
    if pos in ('SB', 'EP'):
        return 'bad'
    return 'neutral'


def _approx_open_pct(pos: str) -> int:
    """Approximate open-raise percentage for position label."""
    return {'BTN': 65, 'CO': 50, 'MP': 35, 'EP': 22, 'SB': 45, 'BB': 0}.get(pos, 35)

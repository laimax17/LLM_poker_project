"""
Learning Mode tracker for the human player.

Records each human decision point, grades it against the GTO baseline
produced by GTOCoach, and accumulates session-level statistics
(VPIP / PFR / aggression) plus simple leak detection.

All grading is a heuristic approximation of GTO — NOT a solver-exact
evaluation. The UI surfaces this caveat to avoid over-trusting the grade.

No LLM and no network required: everything here is pure Python over the
public game state and the (offline) GTOCoach recommendation.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ─── Card display helpers (mirror gto_coach._card_str, but for state dicts) ──────

_RANK_CHAR = {
    14: 'A', 13: 'K', 12: 'Q', 11: 'J', 10: 'T',
    9: '9', 8: '8', 7: '7', 6: '6', 5: '5', 4: '4', 3: '3', 2: '2',
}
_SUIT_CHAR = {
    'Hearts': '♥', 'Diamonds': '♦', 'Clubs': '♣', 'Spades': '♠',
}


def _card_to_str(card: Optional[dict[str, Any]]) -> str:
    if not card:
        return ''
    try:
        r = _RANK_CHAR.get(int(card['rank']), str(card['rank']))
        s = _SUIT_CHAR.get(str(card['suit']), str(card['suit'])[:1])
        return f'{r}{s}'
    except (KeyError, ValueError, TypeError):
        return ''


def _cards_to_str(cards: list[Optional[dict[str, Any]]]) -> str:
    parts = [_card_to_str(c) for c in (cards or [])]
    return ' '.join(p for p in parts if p)


# ─── Grading ─────────────────────────────────────────────────────────────────

# Normalise an engine action to a comparable recommendation token.
_ACTION_TO_REC = {
    'fold': 'FOLD',
    'check': 'CHECK',
    'call': 'CALL',
    'raise': 'RAISE',
    'allin': 'RAISE',
}

# Grade matrix: (gto_recommendation, normalised_action) -> grade.
# Anything not listed defaults to 'marginal'.
_GRADE_MATRIX: dict[tuple[str, str], str] = {
    # GTO says FOLD
    ('FOLD', 'FOLD'): 'correct',
    ('FOLD', 'CHECK'): 'correct',   # checking for free is fine
    ('FOLD', 'CALL'): 'mistake',    # calling a hand that should fold
    ('FOLD', 'RAISE'): 'marginal',  # a bluff — sometimes fine
    # GTO says CHECK
    ('CHECK', 'CHECK'): 'correct',
    ('CHECK', 'CALL'): 'marginal',
    ('CHECK', 'RAISE'): 'marginal',
    ('CHECK', 'FOLD'): 'mistake',   # folding when you could check for free
    # GTO says CALL
    ('CALL', 'CALL'): 'correct',
    ('CALL', 'RAISE'): 'marginal',
    ('CALL', 'CHECK'): 'marginal',
    ('CALL', 'FOLD'): 'mistake',    # folding a +EV call
    # GTO says RAISE
    ('RAISE', 'RAISE'): 'correct',
    ('RAISE', 'CALL'): 'marginal',
    ('RAISE', 'CHECK'): 'marginal',
    ('RAISE', 'FOLD'): 'mistake',   # folding a raise-worthy hand
}

_ACTION_CN = {
    'fold': '弃牌', 'check': '过牌', 'call': '跟注',
    'raise': '加注', 'allin': '全下',
}


def grade_decision(recommendation: str, action: str) -> str:
    """Return 'correct' | 'marginal' | 'mistake' for an action vs the GTO rec."""
    rec = (recommendation or 'CHECK').upper()
    norm = _ACTION_TO_REC.get((action or '').lower(), 'CHECK')
    return _GRADE_MATRIX.get((rec, norm), 'marginal')


# ─── Records ─────────────────────────────────────────────────────────────────

@dataclass
class DecisionRecord:
    street: str
    hand_str: str
    board_str: str
    pot: int
    to_call: int
    recommendation: str
    recommended_amount: Optional[int]
    position: str
    action: str
    amount: int
    grade: str
    explanation: str

    def to_dict(self) -> dict[str, Any]:
        return {
            'street': self.street,
            'handStr': self.hand_str,
            'boardStr': self.board_str,
            'pot': self.pot,
            'toCall': self.to_call,
            'recommendation': self.recommendation,
            'recommendedAmount': self.recommended_amount,
            'position': self.position,
            'action': self.action,
            'amount': self.amount,
            'grade': self.grade,
            'explanation': self.explanation,
        }


@dataclass
class LearningTracker:
    """Stateful tracker for a single learning session (in-memory)."""

    # Current hand
    current_decisions: list[DecisionRecord] = field(default_factory=list)
    hand_start_chips: Optional[int] = None
    hand_number: int = 0
    _finalized: bool = True   # True until a hand is begun

    # Session aggregates
    hands_played: int = 0
    vpip_hands: int = 0          # hands where human voluntarily put money in preflop
    pfr_hands: int = 0           # hands where human raised preflop
    bets_raises: int = 0         # count of raise actions (any street)
    calls: int = 0               # count of call actions (any street)
    net_chips: int = 0
    grade_counts: dict[str, int] = field(
        default_factory=lambda: {'correct': 0, 'marginal': 0, 'mistake': 0}
    )
    # Track specific leak signals
    fold_when_should_call: int = 0   # rec CALL/CHECK but folded
    call_when_should_fold: int = 0   # rec FOLD but called

    def reset(self) -> None:
        """Reset the entire session (e.g. on new game)."""
        self.current_decisions = []
        self.hand_start_chips = None
        self.hand_number = 0
        self._finalized = True
        self.hands_played = 0
        self.vpip_hands = 0
        self.pfr_hands = 0
        self.bets_raises = 0
        self.calls = 0
        self.net_chips = 0
        self.grade_counts = {'correct': 0, 'marginal': 0, 'mistake': 0}
        self.fold_when_should_call = 0
        self.call_when_should_fold = 0

    # ── Per-hand lifecycle ──────────────────────────────────────────────────

    def begin_hand(self, start_chips: int) -> None:
        self.current_decisions = []
        self.hand_start_chips = start_chips
        self._finalized = False
        self.hand_number += 1

    def record_decision(
        self,
        hint: dict[str, Any],
        state: dict[str, Any],
        action: str,
        amount: int,
    ) -> None:
        """Record a single human decision, graded against the GTO hint.

        `hint` is the dict returned by GTOCoach.analyze() (recommendation,
        recommendedAmount, body, stats). `state` is the public game state
        captured *before* the action is applied to the engine.
        """
        if self._finalized:
            # No active hand (defensive) — start one implicitly.
            self.begin_hand(_human_chips(state))

        rec = str(hint.get('recommendation', 'CHECK')).upper()
        rec_amount = hint.get('recommendedAmount')
        street = str(state.get('state', 'PREFLOP'))

        me = _human(state)
        hand_str = _cards_to_str(me.get('hand', []) if me else [])
        board_str = _cards_to_str(state.get('community_cards', []))
        pot = int(state.get('pot', 0))
        current_bet = int(state.get('current_bet', 0))
        my_bet = int(me.get('current_bet', 0)) if me else 0
        to_call = max(0, current_bet - my_bet)

        position = _stat_value(hint, ('位置', 'Position')) or '—'

        grade = grade_decision(rec, action)
        explanation = self._explain(rec, action, hint)

        self.current_decisions.append(DecisionRecord(
            street=street,
            hand_str=hand_str,
            board_str=board_str,
            pot=pot,
            to_call=to_call,
            recommendation=rec,
            recommended_amount=rec_amount,
            position=position,
            action=action,
            amount=int(amount),
            grade=grade,
            explanation=explanation,
        ))

        # ── Update aggregates that depend on the individual action ──
        self.grade_counts[grade] = self.grade_counts.get(grade, 0) + 1

        norm = _ACTION_TO_REC.get((action or '').lower(), 'CHECK')
        if norm == 'RAISE':
            self.bets_raises += 1
        elif norm == 'CALL':
            self.calls += 1

        if rec in ('CALL', 'CHECK') and norm == 'FOLD':
            self.fold_when_should_call += 1
        if rec == 'FOLD' and norm == 'CALL':
            self.call_when_should_fold += 1

    def finalize_hand(self, end_chips: int) -> Optional[dict[str, Any]]:
        """Finalise the current hand; returns a HandReview dict or None.

        Returns None if there is nothing to review (no human decisions and
        already finalised), so callers can avoid emitting empty reviews.
        """
        if self._finalized:
            return None
        self._finalized = True
        self.hands_played += 1

        net = 0
        if self.hand_start_chips is not None:
            net = end_chips - self.hand_start_chips
            self.net_chips += net

        # VPIP / PFR — derive from preflop decisions this hand.
        preflop = [d for d in self.current_decisions if d.street == 'PREFLOP']
        voluntary = any(
            _ACTION_TO_REC.get(d.action.lower(), 'CHECK') in ('CALL', 'RAISE')
            for d in preflop
        )
        raised = any(
            _ACTION_TO_REC.get(d.action.lower(), 'CHECK') == 'RAISE'
            for d in preflop
        )
        if voluntary:
            self.vpip_hands += 1
        if raised:
            self.pfr_hands += 1

        review = {
            'handNumber': self.hand_number,
            'netChips': net,
            'decisions': [d.to_dict() for d in self.current_decisions],
        }
        return review

    # ── Session-level reporting ─────────────────────────────────────────────

    def session_stats(self) -> dict[str, Any]:
        hp = max(1, self.hands_played)
        vpip = self.vpip_hands / hp
        pfr = self.pfr_hands / hp
        af = self.bets_raises / self.calls if self.calls > 0 else (
            float(self.bets_raises) if self.bets_raises else 0.0
        )
        return {
            'handsPlayed': self.hands_played,
            'vpip': round(vpip, 3),
            'pfr': round(pfr, 3),
            'aggressionFactor': round(af, 2),
            'netChips': self.net_chips,
            'correct': self.grade_counts.get('correct', 0),
            'marginal': self.grade_counts.get('marginal', 0),
            'mistake': self.grade_counts.get('mistake', 0),
            'leaks': self.detect_leaks(),
        }

    def detect_leaks(self) -> list[dict[str, str]]:
        """Return a list of {text, severity} leak hints (Chinese)."""
        leaks: list[dict[str, str]] = []
        if self.hands_played < 3:
            return leaks  # not enough data to be meaningful

        hp = self.hands_played
        vpip = self.vpip_hands / hp
        pfr = self.pfr_hands / hp

        if vpip > 0.40:
            leaks.append({
                'text': f'入池率偏高（VPIP {vpip:.0%}）：翻前玩太松，建议收紧起手牌范围，多弃边缘牌。',
                'severity': 'bad',
            })
        elif vpip < 0.15 and hp >= 6:
            leaks.append({
                'text': f'入池率偏低（VPIP {vpip:.0%}）：打得过紧，可在后位适当扩大开牌范围。',
                'severity': 'neutral',
            })

        if self.vpip_hands > 0 and pfr / max(0.01, vpip) < 0.5:
            leaks.append({
                'text': '过于被动：翻前跟注远多于加注，强牌应多用加注施压而非平跟。',
                'severity': 'bad',
            })

        decisions_total = sum(self.grade_counts.values())
        if decisions_total >= 8:
            mistake_rate = self.grade_counts.get('mistake', 0) / decisions_total
            if self.call_when_should_fold >= 2 and \
                    self.call_when_should_fold >= self.fold_when_should_call:
                leaks.append({
                    'text': '跟注过多（calling station 倾向）：胜率不足/位置劣势时仍跟注，是主要漏洞。',
                    'severity': 'bad',
                })
            if self.fold_when_should_call >= 2 and \
                    self.fold_when_should_call > self.call_when_should_fold:
                leaks.append({
                    'text': '弃牌过头：面对下注时放弃了底池赔率合适的跟注，错失了 +EV 机会。',
                    'severity': 'bad',
                })
            if mistake_rate < 0.15:
                leaks.append({
                    'text': f'决策质量良好：失误率仅 {mistake_rate:.0%}，继续保持。',
                    'severity': 'good',
                })

        return leaks

    # ── Internal ────────────────────────────────────────────────────────────

    @staticmethod
    def _explain(rec: str, action: str, hint: dict[str, Any]) -> str:
        action_cn = _ACTION_CN.get((action or '').lower(), action)
        head = f'GTO 建议 {rec}，你选择了{action_cn}。'
        body = str(hint.get('body', '')).strip()
        # Take the first informative line of the coach body as the rationale.
        first_line = ''
        for line in body.split('\n'):
            line = line.strip()
            if line and not line.startswith('【') and not line.startswith('GTO 要点'):
                first_line = line
                break
        return f'{head} {first_line}'.strip()


# ─── State helpers ─────────────────────────────────────────────────────────────

def _human(state: dict[str, Any]) -> Optional[dict[str, Any]]:
    for p in state.get('players', []):
        if p.get('id') == 'human':
            return p
    return None


def _human_chips(state: dict[str, Any]) -> int:
    me = _human(state)
    return int(me.get('chips', 0)) if me else 0


def _stat_value(hint: dict[str, Any], labels: tuple[str, ...]) -> Optional[str]:
    """Find a stat value by matching its label against any of `labels`."""
    for s in hint.get('stats', []):
        label = str(s.get('label', ''))
        if any(lbl in label for lbl in labels):
            return str(s.get('value', ''))
    return None

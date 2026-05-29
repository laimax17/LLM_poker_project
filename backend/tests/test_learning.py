"""Tests for the Learning Mode tracker (src/learning.py)."""
from backend.src.learning import LearningTracker, grade_decision, _cards_to_str


# ─── grade_decision ────────────────────────────────────────────────────────────

def test_grade_exact_match_is_correct():
    assert grade_decision('FOLD', 'fold') == 'correct'
    assert grade_decision('CALL', 'call') == 'correct'
    assert grade_decision('RAISE', 'raise') == 'correct'
    assert grade_decision('CHECK', 'check') == 'correct'


def test_grade_allin_counts_as_raise():
    assert grade_decision('RAISE', 'allin') == 'correct'


def test_grade_call_when_should_fold_is_mistake():
    assert grade_decision('FOLD', 'call') == 'mistake'


def test_grade_fold_when_should_call_is_mistake():
    assert grade_decision('CALL', 'fold') == 'mistake'


def test_grade_fold_when_could_check_is_mistake():
    assert grade_decision('CHECK', 'fold') == 'mistake'


def test_grade_more_aggressive_than_recommended_is_marginal():
    assert grade_decision('CALL', 'raise') == 'marginal'
    assert grade_decision('CHECK', 'raise') == 'marginal'


def test_grade_handles_unknown_action():
    # Unknown actions normalise to CHECK; (RAISE, CHECK) -> marginal
    assert grade_decision('RAISE', 'banana') == 'marginal'


# ─── Card formatting ───────────────────────────────────────────────────────────

def test_cards_to_str():
    cards = [{'rank': 14, 'suit': 'Spades'}, {'rank': 13, 'suit': 'Hearts'}]
    assert _cards_to_str(cards) == 'A♠ K♥'


def test_cards_to_str_empty():
    assert _cards_to_str([]) == ''
    assert _cards_to_str([None]) == ''


# ─── Test fixtures ─────────────────────────────────────────────────────────────

def _state(street='PREFLOP', chips=5000, current_bet=0, my_bet=0, pot=30,
           hand=None, community=None):
    return {
        'state': street,
        'pot': pot,
        'current_bet': current_bet,
        'community_cards': community or [],
        'players': [
            {
                'id': 'human',
                'chips': chips,
                'current_bet': my_bet,
                'is_active': True,
                'hand': hand or [{'rank': 14, 'suit': 'Spades'},
                                 {'rank': 14, 'suit': 'Hearts'}],
            },
            {'id': 'bot_1', 'chips': 5000, 'current_bet': current_bet,
             'is_active': True, 'hand': [None, None]},
        ],
    }


def _hint(rec='RAISE', amount=100, equity='80%'):
    return {
        'recommendation': rec,
        'recommendedAmount': amount,
        'body': '【翻牌前分析】手牌：A♠ A♥\n这是一手强起手牌，建议开注。\nGTO 要点：',
        'stats': [
            {'label': '胜率估计', 'value': equity, 'quality': 'good'},
            {'label': '位置', 'value': 'BTN（按钮位）', 'quality': 'good'},
        ],
    }


# ─── Tracker lifecycle ─────────────────────────────────────────────────────────

def test_finalize_without_begin_returns_none():
    t = LearningTracker()
    assert t.finalize_hand(5000) is None


def test_basic_hand_review_structure():
    t = LearningTracker()
    t.begin_hand(5000)
    t.record_decision(_hint('RAISE'), _state(), 'raise', 100)
    review = t.finalize_hand(5100)

    assert review is not None
    assert review['handNumber'] == 1
    assert review['netChips'] == 100
    assert len(review['decisions']) == 1
    d = review['decisions'][0]
    assert d['recommendation'] == 'RAISE'
    assert d['action'] == 'raise'
    assert d['grade'] == 'correct'
    assert d['handStr'] == 'A♠ A♥'
    assert 'GTO 建议 RAISE' in d['explanation']


def test_finalize_is_idempotent():
    t = LearningTracker()
    t.begin_hand(5000)
    t.record_decision(_hint('CALL'), _state(), 'call', 20)
    assert t.finalize_hand(5000) is not None
    assert t.finalize_hand(5000) is None  # second call returns nothing


def test_vpip_and_pfr_tracking():
    t = LearningTracker()
    # Hand 1: raise preflop → counts for both VPIP and PFR
    t.begin_hand(5000)
    t.record_decision(_hint('RAISE'), _state(), 'raise', 100)
    t.finalize_hand(5200)
    # Hand 2: fold preflop → neither
    t.begin_hand(5200)
    t.record_decision(_hint('FOLD'), _state(), 'fold', 0)
    t.finalize_hand(5180)

    stats = t.session_stats()
    assert stats['handsPlayed'] == 2
    assert stats['vpip'] == 0.5   # 1 of 2 hands voluntary
    assert stats['pfr'] == 0.5    # 1 of 2 hands raised


def test_aggression_factor():
    t = LearningTracker()
    t.begin_hand(5000)
    t.record_decision(_hint('RAISE'), _state(), 'raise', 100)
    t.record_decision(_hint('CALL'), _state(street='FLOP'), 'call', 50)
    t.record_decision(_hint('RAISE'), _state(street='TURN'), 'raise', 100)
    t.finalize_hand(5000)
    stats = t.session_stats()
    # 2 raises / 1 call = 2.0
    assert stats['aggressionFactor'] == 2.0


def test_leak_detection_high_vpip():
    t = LearningTracker()
    # Play 5 loose hands (always call preflop) → high VPIP, no raises
    for i in range(5):
        t.begin_hand(5000)
        t.record_decision(_hint('FOLD'), _state(), 'call', 20)
        t.finalize_hand(4980)
    leaks = t.detect_leaks()
    texts = ' '.join(leak['text'] for leak in leaks)
    assert 'VPIP' in texts or '入池' in texts


def test_no_leaks_with_insufficient_data():
    t = LearningTracker()
    t.begin_hand(5000)
    t.record_decision(_hint('CALL'), _state(), 'call', 20)
    t.finalize_hand(5000)
    assert t.detect_leaks() == []  # < 3 hands


def test_reset_clears_session():
    t = LearningTracker()
    t.begin_hand(5000)
    t.record_decision(_hint('RAISE'), _state(), 'raise', 100)
    t.finalize_hand(5100)
    t.reset()
    stats = t.session_stats()
    assert stats['handsPlayed'] == 0
    assert stats['netChips'] == 0
    assert t.finalize_hand(5000) is None

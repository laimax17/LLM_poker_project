"""Tests for agent bot pieces: opponent model + spot analytics."""
from backend.src.ai.opponent_model import OpponentModel
from backend.src.ai.analytics import compute_analytics


# ─── OpponentModel ─────────────────────────────────────────────────────────────

def _play_hand(om, observations):
    om.begin_hand()
    for pid, street, action in observations:
        om.observe(pid, street, action)
    om.commit_hand()


def test_unknown_until_enough_hands():
    om = OpponentModel()
    _play_hand(om, [('bot_1', 'PREFLOP', 'raise')])
    _play_hand(om, [('bot_1', 'PREFLOP', 'raise')])
    # < 3 hands → unknown
    assert om.profile('bot_1')['label'] == 'unknown'


def test_classify_lag():
    om = OpponentModel()
    for _ in range(5):
        _play_hand(om, [('bot_1', 'PREFLOP', 'raise'), ('bot_1', 'FLOP', 'raise')])
    prof = om.profile('bot_1')
    assert prof['label'].startswith('LAG')
    assert prof['vpip'] == 1.0
    assert prof['pfr'] == 1.0


def test_classify_rock():
    om = OpponentModel()
    for _ in range(5):
        _play_hand(om, [('bot_1', 'PREFLOP', 'fold')])
    assert om.profile('bot_1')['label'].startswith('rock')


def test_classify_station():
    om = OpponentModel()
    # loose (calls a lot) but passive (no raises)
    for _ in range(5):
        _play_hand(om, [('bot_1', 'PREFLOP', 'call'), ('bot_1', 'FLOP', 'call')])
    prof = om.profile('bot_1')
    assert prof['label'].startswith('station')
    assert prof['vpip'] == 1.0
    assert prof['pfr'] == 0.0


def test_profiles_except_filters_self_and_inactive():
    om = OpponentModel()
    for _ in range(3):
        _play_hand(om, [
            ('bot_1', 'PREFLOP', 'raise'),
            ('bot_2', 'PREFLOP', 'call'),
            ('human', 'PREFLOP', 'fold'),
        ])
    profs = om.profiles_except('bot_1', only_active=['bot_1', 'bot_2'])
    assert 'bot_1' not in profs       # self excluded
    assert 'bot_2' in profs           # active included
    assert 'human' not in profs       # not in active set


def test_reset_clears_all():
    om = OpponentModel()
    for _ in range(4):
        _play_hand(om, [('bot_1', 'PREFLOP', 'raise')])
    om.reset()
    assert om.profile('bot_1')['hands'] == 0


# ─── Analytics ─────────────────────────────────────────────────────────────────

def _preflop_state():
    return {
        'state': 'PREFLOP',
        'pot': 30,
        'current_bet': 20,
        'community_cards': [],
        'min_raise': 20,
        'raise_count': 1,
        'players': [
            {'id': 'bot_1', 'chips': 5000, 'current_bet': 0, 'is_active': True,
             'is_dealer': True,
             'hand': [{'rank': 14, 'suit': 'Spades'}, {'rank': 13, 'suit': 'Spades'}]},
            {'id': 'bot_2', 'chips': 5000, 'current_bet': 20, 'is_active': True,
             'hand': [None, None]},
        ],
    }


def test_analytics_preflop_combo_and_potodds():
    a = compute_analytics(_preflop_state(), 'bot_1')
    assert a['combo'] == 'AKs'
    assert a['position'] == 'BTN'
    assert a['to_call'] == 20
    # pot odds = 20 / (30 + 20)
    assert abs(a['pot_odds'] - 0.4) < 1e-6
    assert 'equity' not in a  # equity only computed post-flop


def test_analytics_postflop_has_equity_and_texture():
    state = _preflop_state()
    state['state'] = 'FLOP'
    state['community_cards'] = [
        {'rank': 12, 'suit': 'Spades'},
        {'rank': 7, 'suit': 'Hearts'},
        {'rank': 2, 'suit': 'Diamonds'},
    ]
    a = compute_analytics(state, 'bot_1')
    assert 'equity' in a and 0.0 <= a['equity'] <= 1.0
    assert 'board_wetness' in a
    assert isinstance(a['board_draws'], list)


def test_analytics_missing_player():
    assert compute_analytics(_preflop_state(), 'nobody') == {}

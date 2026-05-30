"""Tests for the tournament manager (src/tournament.py)."""
from backend.src.tournament import (
    TournamentManager,
    TournamentConfig,
    BLIND_LEVELS,
)


def _mgr(speed='normal', n=5, stack=5000):
    m = TournamentManager()
    m.configure(TournamentConfig(num_opponents=n, starting_stack=stack, blind_speed=speed))
    m.start(total_players=n + 1)
    return m


def test_config_sanitized():
    m = TournamentManager()
    m.configure(TournamentConfig(num_opponents=99, starting_stack=10, blind_speed='x', difficulty='y'))
    assert m.config.num_opponents == 5
    assert m.config.starting_stack == 500
    assert m.config.blind_speed == 'normal'
    assert m.config.difficulty == 'normal'


def test_blinds_start_at_level_one():
    m = _mgr('normal')
    assert m.on_hand_start() is False  # first hand, no level-up
    assert m.current_blinds() == BLIND_LEVELS[0]
    assert m.level == 0


def test_blind_escalation_normal_speed():
    m = _mgr('normal')  # 10 hands per level
    leveled = [m.on_hand_start() for _ in range(11)]
    # hand 11 triggers level-up to level index 1
    assert leveled[10] is True
    assert m.level == 1
    assert m.current_blinds() == BLIND_LEVELS[1]


def test_turbo_speed():
    m = _mgr('turbo')  # 5 hands per level
    for _ in range(5):
        m.on_hand_start()
    assert m.level == 0
    assert m.on_hand_start() is True  # hand 6 → level 1
    assert m.level == 1


def test_hands_until_next_level():
    m = _mgr('normal')
    m.on_hand_start()  # hand 1
    assert m.hands_until_next_level() == 9
    for _ in range(9):
        m.on_hand_start()  # through hand 10
    assert m.hands_until_next_level() == 0  # next hand levels up


def test_blinds_cap_at_top_level():
    m = _mgr('turbo')
    for _ in range(500):
        m.on_hand_start()
    assert m.current_blinds() == BLIND_LEVELS[-1]
    assert m.hands_until_next_level() == 0


def test_elimination_records_place():
    m = _mgr('normal', n=5)  # 6 players
    players = [
        {'id': 'human', 'name': 'P', 'chips': 5000},
        {'id': 'bot_1', 'name': 'A', 'chips': 5000},
        {'id': 'bot_2', 'name': 'B', 'chips': 0},  # busts
        {'id': 'bot_3', 'name': 'C', 'chips': 5000},
        {'id': 'bot_4', 'name': 'D', 'chips': 5000},
        {'id': 'bot_5', 'name': 'E', 'chips': 5000},
    ]
    newly = m.record_eliminations(players)
    assert len(newly) == 1
    assert newly[0]['id'] == 'bot_2'
    assert newly[0]['place'] == 6  # finished last (6th)
    # idempotent — not recorded twice
    assert m.record_eliminations(players) == []


def test_tournament_over_and_final_standings():
    m = _mgr('normal', n=1)  # heads-up: 2 players
    players = [
        {'id': 'human', 'name': 'P', 'chips': 10000},
        {'id': 'bot_1', 'name': 'A', 'chips': 0},
    ]
    m.record_eliminations(players)
    assert m.is_over(players) is True
    standings = m.final_standings(players)
    assert standings[0]['id'] == 'human' and standings[0]['place'] == 1
    assert standings[1]['id'] == 'bot_1' and standings[1]['place'] == 2


def test_place_of_chip_leader():
    m = _mgr('normal', n=2)
    players = [
        {'id': 'human', 'name': 'P', 'chips': 8000},
        {'id': 'bot_1', 'name': 'A', 'chips': 5000},
        {'id': 'bot_2', 'name': 'B', 'chips': 2000},
    ]
    assert m.place_of('human', players) == 1
    assert m.place_of('bot_2', players) == 3


def test_state_payload_shape():
    m = _mgr('normal')
    m.on_hand_start()
    players = [{'id': 'human', 'name': 'P', 'chips': 5000}] + \
              [{'id': f'bot_{i}', 'name': f'B{i}', 'chips': 5000} for i in range(1, 6)]
    p = m.state_payload(players, 'human')
    assert p['active'] is True
    assert p['level'] == 1
    assert p['smallBlind'] == BLIND_LEVELS[0][0]
    assert p['playersRemaining'] == 6
    assert p['totalPlayers'] == 6
    assert p['yourPlace'] >= 1

"""
Tournament manager.

Adds a real single-table tournament structure on top of the poker engine
*without* touching engine.py: blinds escalate by level, busted players are
ranked by elimination order, and the tournament ends when one player remains.

The engine exposes mutable `small_blind` / `big_blind` attributes that it reads
at start_hand(), so escalation is just "set the blinds before the next hand".
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

# Standard escalating blind ladder; holds at the top level.
BLIND_LEVELS: list[tuple[int, int]] = [
    (10, 20), (15, 30), (25, 50), (50, 100), (75, 150), (100, 200),
    (150, 300), (200, 400), (300, 600), (500, 1000), (750, 1500), (1000, 2000),
]

# blind_speed -> hands per level
SPEED_HANDS_PER_LEVEL: dict[str, int] = {'turbo': 5, 'normal': 10, 'slow': 20}

# difficulty -> bot engine
DIFFICULTY_ENGINE: dict[str, str] = {
    'easy': 'rule-based',
    'normal': 'gto',
    'hard': 'gto',
}


@dataclass
class TournamentConfig:
    num_opponents: int = 5
    starting_stack: int = 5000
    blind_speed: str = 'normal'
    difficulty: str = 'normal'

    def sanitized(self) -> 'TournamentConfig':
        return TournamentConfig(
            num_opponents=max(1, min(5, int(self.num_opponents))),
            starting_stack=max(500, min(100000, int(self.starting_stack))),
            blind_speed=self.blind_speed if self.blind_speed in SPEED_HANDS_PER_LEVEL else 'normal',
            difficulty=self.difficulty if self.difficulty in DIFFICULTY_ENGINE else 'normal',
        )


@dataclass
class TournamentManager:
    config: TournamentConfig = field(default_factory=TournamentConfig)
    active: bool = False
    hand_count: int = 0
    level: int = 0
    total_players: int = 0
    # Elimination order: standings[0] is the FIRST player out (worst place).
    standings: list[str] = field(default_factory=list)
    _busted: set[str] = field(default_factory=set)

    # ── Lifecycle ────────────────────────────────────────────────────────────

    def configure(self, config: TournamentConfig) -> None:
        self.config = config.sanitized()

    def start(self, total_players: int) -> None:
        self.active = True
        self.hand_count = 0
        self.level = 0
        self.total_players = total_players
        self.standings = []
        self._busted = set()

    @property
    def hands_per_level(self) -> int:
        return SPEED_HANDS_PER_LEVEL.get(self.config.blind_speed, 10)

    def engine_for_difficulty(self) -> str:
        return DIFFICULTY_ENGINE.get(self.config.difficulty, 'gto')

    # ── Per-hand ──────────────────────────────────────────────────────────────

    def on_hand_start(self) -> bool:
        """Advance the hand counter, recompute level. Returns True on level-up."""
        self.hand_count += 1
        new_level = min((self.hand_count - 1) // self.hands_per_level, len(BLIND_LEVELS) - 1)
        leveled_up = new_level > self.level
        self.level = new_level
        return leveled_up

    def current_blinds(self) -> tuple[int, int]:
        return BLIND_LEVELS[min(self.level, len(BLIND_LEVELS) - 1)]

    def hands_until_next_level(self) -> int:
        if self.level >= len(BLIND_LEVELS) - 1:
            return 0
        if self.hand_count == 0:
            return self.hands_per_level
        return self.hands_per_level - 1 - ((self.hand_count - 1) % self.hands_per_level)

    # ── Eliminations & standings ───────────────────────────────────────────────

    def record_eliminations(self, players: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Scan for newly-busted players (chips == 0); record their place.

        `players` is a list of dicts with at least 'id', 'name', 'chips'.
        Returns the newly eliminated players with their finishing place.
        """
        newly: list[dict[str, Any]] = []
        alive_now = sum(1 for p in players if p['chips'] > 0)
        for p in players:
            if p['chips'] <= 0 and p['id'] not in self._busted:
                self._busted.add(p['id'])
                self.standings.append(p['id'])
                # Place = number of players that were still alive *including* this
                # one at the moment of busting = alive_now + (#busted this scan so far)
                place = alive_now + len([x for x in newly]) + 1
                entry = {'id': p['id'], 'name': p['name'], 'place': place}
                newly.append(entry)
        return newly

    def is_over(self, players: list[dict[str, Any]]) -> bool:
        alive = sum(1 for p in players if p['chips'] > 0)
        return self.active and alive <= 1

    def final_standings(self, players: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Full ranking: winner first, then busted players in reverse bust order."""
        by_id = {p['id']: p for p in players}
        result: list[dict[str, Any]] = []
        # Survivors (chips > 0) ranked by chips desc, then busted in reverse order.
        survivors = sorted(
            (p for p in players if p['chips'] > 0),
            key=lambda p: p['chips'], reverse=True,
        )
        place = 1
        for p in survivors:
            result.append({'id': p['id'], 'name': p['name'], 'place': place, 'chips': p['chips']})
            place += 1
        for pid in reversed(self.standings):
            p = by_id.get(pid)
            if p:
                result.append({'id': pid, 'name': p['name'], 'place': place, 'chips': 0})
                place += 1
        return result

    def place_of(self, player_id: str, players: list[dict[str, Any]]) -> int:
        """Current standing of a player (1 = chip leader / last remaining)."""
        alive = sorted(
            (p for p in players if p['chips'] > 0),
            key=lambda p: p['chips'], reverse=True,
        )
        for i, p in enumerate(alive):
            if p['id'] == player_id:
                return i + 1
        # Busted: place from standings
        if player_id in self.standings:
            # earlier bust = worse place
            return self.total_players - self.standings.index(player_id)
        return len(alive) + 1

    # ── Payload ────────────────────────────────────────────────────────────────

    def state_payload(self, players: list[dict[str, Any]], for_id: str = 'human') -> dict[str, Any]:
        sb, bb = self.current_blinds()
        alive = sum(1 for p in players if p['chips'] > 0)
        return {
            'active': self.active,
            'level': self.level + 1,
            'smallBlind': sb,
            'bigBlind': bb,
            'handsUntilNextLevel': self.hands_until_next_level(),
            'playersRemaining': alive,
            'totalPlayers': self.total_players,
            'yourPlace': self.place_of(for_id, players),
            'handCount': self.hand_count,
        }

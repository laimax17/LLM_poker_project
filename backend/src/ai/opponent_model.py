"""
Opponent modeling — the agent's memory.

Tracks every player's observed tendencies across the session (VPIP, PFR,
post-flop aggression) and distils them into a short read the LLM agent can use
to exploit opponents. This is what turns a one-shot decision into something
"agentic": the bot remembers how you and the other bots have been playing.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PlayerStats:
    hands_seen: int = 0          # hands where the player took a preflop action
    vpip_hands: int = 0          # hands voluntarily entering the pot
    pfr_hands: int = 0           # hands raising preflop
    bets_raises: int = 0
    calls: int = 0
    # Per-hand flags (reset each hand)
    _seen_this_hand: bool = False
    _vpip_this_hand: bool = False
    _pfr_this_hand: bool = False

    def reset_hand(self) -> None:
        self._seen_this_hand = False
        self._vpip_this_hand = False
        self._pfr_this_hand = False

    def commit_hand(self) -> None:
        if self._seen_this_hand:
            self.hands_seen += 1
        if self._vpip_this_hand:
            self.vpip_hands += 1
        if self._pfr_this_hand:
            self.pfr_hands += 1


class OpponentModel:
    """Session-long observation store for all players."""

    def __init__(self) -> None:
        self._stats: dict[str, PlayerStats] = {}

    def reset(self) -> None:
        self._stats = {}

    def _get(self, player_id: str) -> PlayerStats:
        if player_id not in self._stats:
            self._stats[player_id] = PlayerStats()
        return self._stats[player_id]

    def begin_hand(self) -> None:
        for s in self._stats.values():
            s.reset_hand()

    def commit_hand(self) -> None:
        for s in self._stats.values():
            s.commit_hand()

    def observe(self, player_id: str, street: str, action: str) -> None:
        """Record one action (street captured *before* it is applied)."""
        s = self._get(player_id)
        a = (action or '').lower()
        if street == 'PREFLOP':
            s._seen_this_hand = True
            if a in ('call', 'raise', 'allin'):
                s._vpip_this_hand = True
            if a in ('raise', 'allin'):
                s._pfr_this_hand = True
        if a in ('raise', 'allin'):
            s.bets_raises += 1
        elif a == 'call':
            s.calls += 1

    # ── Reads ────────────────────────────────────────────────────────────────

    def profile(self, player_id: str) -> dict[str, Any]:
        s = self._stats.get(player_id)
        if s is None or s.hands_seen < 3:
            return {'label': 'unknown', 'hands': s.hands_seen if s else 0}
        vpip = s.vpip_hands / s.hands_seen
        pfr = s.pfr_hands / s.hands_seen
        af = s.bets_raises / s.calls if s.calls else float(s.bets_raises)
        return {
            'label': _classify(vpip, pfr, af),
            'hands': s.hands_seen,
            'vpip': round(vpip, 2),
            'pfr': round(pfr, 2),
            'af': round(af, 1),
        }

    def profiles_except(self, player_id: str, only_active: list[str] | None = None) -> dict[str, dict[str, Any]]:
        """Profiles of every other tracked player (optionally filtered to a set)."""
        out: dict[str, dict[str, Any]] = {}
        for pid in self._stats:
            if pid == player_id:
                continue
            if only_active is not None and pid not in only_active:
                continue
            out[pid] = self.profile(pid)
        return out


def _classify(vpip: float, pfr: float, af: float) -> str:
    """Map stats to a familiar player-type label."""
    loose = vpip >= 0.30
    aggressive = pfr >= 0.18 and af >= 1.5
    if loose and aggressive:
        return 'LAG (loose-aggressive)'
    if not loose and aggressive:
        return 'TAG (tight-aggressive)'
    if loose and not aggressive:
        return 'station (loose-passive)'
    return 'rock (tight-passive)'

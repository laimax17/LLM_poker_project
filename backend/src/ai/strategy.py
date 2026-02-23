"""
Abstract base class for bot decision strategies.
All bot strategies must implement this interface.
"""
import logging
from abc import ABC, abstractmethod
from typing import Any

from ..schemas import AIThought

logger = logging.getLogger(__name__)


class BotStrategy(ABC):
    """Abstract base class for all bot decision-making strategies."""

    @abstractmethod
    def decide(self, game_state: dict[str, Any], player_id: str) -> AIThought:
        """
        Given the full game state (from engine.get_public_game_state(player_id))
        and the player_id of the bot making a decision, return an AIThought
        containing the chosen action, optional amount, thought, and chat message.
        """
        ...

    @property
    def name(self) -> str:
        """Human-readable strategy name for logging."""
        return self.__class__.__name__

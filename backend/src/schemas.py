from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from enum import Enum

class Suit(str, Enum):
    HEARTS = "Hearts"
    DIAMONDS = "Diamonds"
    CLUBS = "Clubs"
    SPADES = "Spades"

class Rank(int, Enum):
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14

class CardModel(BaseModel):
    rank: int
    suit: str
    
    class Config:
        use_enum_values = True

class PlayerModel(BaseModel):
    id: str
    name: str
    chips: int
    hand: List[Optional[CardModel]] = []
    is_active: bool
    current_bet: int
    is_all_in: bool
    has_acted: bool = False
    is_dealer: bool = False
    is_turn: bool = False

class GameStateModel(BaseModel):
    state: str
    pot: int
    community_cards: List[CardModel]
    players: List[PlayerModel]
    current_player_idx: int
    current_bet: int
    min_raise: int = 0
    winners: List[str] = []
    winning_hand: str = ""

class ActionType(str, Enum):
    FOLD = "fold"
    CHECK = "check"
    CALL = "call"
    RAISE = "raise"
    ALLIN = "allin"

class ActionRequest(BaseModel):
    action: ActionType
    amount: int = 0 

class AIThought(BaseModel):
    action: str
    amount: int
    thought: str
    chat_message: str

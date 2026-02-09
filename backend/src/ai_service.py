import os
import json
import random
from typing import Dict, Any, Optional
from .engine import HandEvaluator, Card, Rank, Suit
from .schemas import GameStateModel, PlayerModel, ActionRequest, ActionType, AIThought

class AIAgent:
    def __init__(self, player_id: str, mode: str = "algo", personality: str = "balanced"):
        self.player_id = player_id
        self.mode = mode # 'algo' or 'llm'
        self.personality = personality
        self.api_key = os.getenv("LLM_API_KEY", "")

    def decide(self, game_state: Dict[str, Any]) -> AIThought:
        # User requested Simple Rule Bot
        return self.decide_simple(game_state)

    def decide_simple(self, game_state: Dict[str, Any]) -> AIThought:
        # Parse state
        players = game_state["players"]
        my_player = next((p for p in players if p["id"] == self.player_id), None)
        
        # If I am not found or eliminated
        if not my_player or not my_player.get("is_active"):
             return AIThought(action="fold", amount=0, thought="I am out", chat_message="")

        current_bet = game_state["current_bet"]
        my_bet = my_player["current_bet"]
        to_call = current_bet - my_bet
        min_raise = game_state["min_raise"]
        chips = my_player["chips"]
        
        # 1. Check if available
        if to_call == 0:
            return AIThought(action="check", amount=0, thought="Checking free card", chat_message="Check.")
        
        # 2. Call if bet is small (< 10% of chips?)
        # "If Bet is small: Call."
        # Let's say small is < 5% of starting stack (1000) -> 50 chips.
        if to_call < 50:
             return AIThought(action="call", amount=0, thought="Small bet, calling", chat_message="I call.")
             
        # 3. If bet is large & Hand is weak: Fold.
        # Check hand strength - we need to see our own cards!
        # Game state 'hand' might be None if masked?
        # But we are the AI, running in backend. 
        # The engine should pass us the FULL state if possible, or we should have access.
        # Wait, determine if game_state has masked cards.
        # If game_state was generated for "human", then AI cards are masked!
        # Bug: Main.py passes `engine.get_game_state()` which is now `get_public_game_state`??
        # I need to update main.py to pass specific state to AI, or just pass the Engine object?
        # Or `engine.get_public_game_state(ai_id)`.
        
        # If we can't see cards, we assume weak hand and fold to big bets.
        hand = my_player.get("hand")
        if hand and None not in hand:
             # Evaluate
             my_cards = [Card(Rank(c["rank"]), Suit(c["suit"])) for c in hand]
             # Just high card check for "Simple"
             has_high_card = any(c.rank >= Rank.QUEEN for c in my_cards)
             if has_high_card:
                  return AIThought(action="call", amount=0, thought="High card, calling", chat_message="Let's see.")
        
        return AIThought(action="fold", amount=0, thought="Bet too big", chat_message="Too rich for me.")

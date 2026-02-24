import pytest
import sys
import os

# Ensure backend/src is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.engine import (
    PokerEngine, Card, Rank, Suit,
    HandEvaluator, HandRank, Player, GameState,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _setup_game(player_configs, dealer_idx_before_rotation=1):
    """Setup a game with specific player chips."""
    engine = PokerEngine()
    for p_id, name, chips in player_configs:
        engine.add_player(p_id, name, chips)
    # Control dealer. start_hand() rotates it.
    engine.dealer_idx = dealer_idx_before_rotation
    engine.start_hand() 
    return engine

def _act(engine, player_id, action, amount=0):
    """Wrapper for player_action."""
    engine.player_action(player_id, action, amount)

# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------

def test_scenario_1_value_bet_to_showdown():
    """
    Scenario 1: Standard Value Bet to Showdown
    - 2 Players: P1 (Alice), P2 (Bob)
    - Alice is Dealer (BB), Bob is SB.
    - Pre-flop: Bob calls, Alice checks.
    - Flop: Both check.
    - Turn: Bob checks, Alice bets 40, Bob calls.
    - River: Bob checks, Alice bets 100, Bob calls.
    - Showdown: Alice wins with Pair of Aces.
    """
    # dealer_idx=1 before rotation -> dealer=0 (Alice) after start_hand
    engine = _setup_game([("p1", "Alice", 1000), ("p2", "Bob", 1000)], 1)
    
    # Alice (p1): AA
    engine.players[0].hand = [Card(Rank.ACE, Suit.HEARTS), Card(Rank.ACE, Suit.DIAMONDS)]
    # Bob (p2): KK
    engine.players[1].hand = [Card(Rank.KING, Suit.HEARTS), Card(Rank.KING, Suit.DIAMONDS)]
    
    # Pre-flop: Bob (SB) acts first
    _act(engine, "p2", "call")
    _act(engine, "p1", "check")
    assert engine.state == GameState.FLOP
    
    # To keep board clean, we inject board after street transition
    engine.community_cards = [Card(Rank.TWO, Suit.CLUBS), Card(Rank.FIVE, Suit.SPADES), Card(Rank.NINE, Suit.DIAMONDS)]
    
    # Flop: Bob (SB) acts first
    _act(engine, "p2", "check")
    _act(engine, "p1", "check")
    assert engine.state == GameState.TURN
    
    # Turn: override the card dealt by engine
    engine.community_cards[-1] = Card(Rank.JACK, Suit.CLUBS)
    _act(engine, "p2", "check")
    _act(engine, "p1", "raise", 40)
    _act(engine, "p2", "call")
    assert engine.state == GameState.RIVER
    
    # River: override the card dealt by engine
    engine.community_cards[-1] = Card(Rank.THREE, Suit.DIAMONDS)
    _act(engine, "p2", "check")
    _act(engine, "p1", "raise", 100)
    _act(engine, "p2", "call")
    
    assert engine.state == GameState.FINISHED
    assert engine.winning_hand_rank == "Pair"
    assert "p1" in engine.winners
    
    # Alice (p1) started with 1000. 
    # Alice was BB (20). Turn bet 40. River bet 100. Total in = 160.
    # Bob (p2) was SB (10). Pre-flop call (10). Turn call (40). River call (100). Total in = 160.
    # Pot = 320. Alice wins 320. Total = 1000 - 160 + 320 = 1160.
    assert engine.players[0].chips == 1160
    assert engine.players[1].chips == 840

def test_scenario_2_aggressive_bluff_fold():
    """
    Scenario 2: High-Stakes Bluff
    - Bob (SB) bluffs Alice (BB).
    - Bob wins without showdown.
    """
    engine = _setup_game([("p1", "Alice", 1000), ("p2", "Bob", 1000)], 1)
    
    # Pre-flop: Bob (SB) raises
    _act(engine, "p2", "raise", 60)
    _act(engine, "p1", "call")
    
    # Flop: Bob bets
    _act(engine, "p2", "raise", 100)
    _act(engine, "p1", "call")
    
    # Turn: Bob bets
    _act(engine, "p2", "raise", 250)
    _act(engine, "p1", "call")
    
    # River: Bob all-in
    _act(engine, "p2", "allin")
    _act(engine, "p1", "fold")
    
    assert engine.state == GameState.FINISHED
    assert engine.winners == ["p2"]
    assert engine.winning_hand_rank == "Opponents Folded"
    
    # Alice (p1) chips: 1000 - 60(pf) - 100(f) - 250(t) = 590
    assert engine.players[0].chips == 590
    # Bob (p2) chips: 2000 - 590 = 1410
    assert engine.players[1].chips == 1410

def test_scenario_3_short_stack_forced_allin():
    """
    Scenario 3: Short Stack All-in (Fixed Engine)
    - Short is SB with 5 chips. Rich is BB.
    - Rich should act first pre-flop because SB is already all-in.
    """
    engine = PokerEngine()
    engine.add_player("p1", "Rich", 1000)
    engine.add_player("p2", "Short", 5)
    engine.dealer_idx = 1 # Bob (Short) is dealer
    engine.start_hand() # dealer becomes 0 (Rich). SB=Short, BB=Rich.
    
    short = next(p for p in engine.players if p.id == "p2")
    assert short.is_all_in
    assert short.current_bet == 5
    
    # Engine now skips Short and starts with Rich (BB)
    assert engine.players[engine.current_player_idx].id == "p1"
    
    _act(engine, "p1", "check")
    assert engine.state == GameState.FINISHED
    assert len(engine.community_cards) == 5

def test_scenario_4_split_pot_chop():
    """
    Scenario 4: Split Pot (The Chop)
    """
    engine = _setup_game([("p1", "Alice", 1000), ("p2", "Bob", 1000)], 1) # Alice is dealer/BB
    
    # Inject hands
    engine.players[0].hand = [Card(Rank.ACE, Suit.HEARTS), Card(Rank.KING, Suit.DIAMONDS)]
    engine.players[1].hand = [Card(Rank.ACE, Suit.SPADES), Card(Rank.KING, Suit.CLUBS)]
    
    # Move through streets by checking
    _act(engine, "p2", "call") # Bob (SB)
    _act(engine, "p1", "check") # Alice (BB)
    
    # Inject board for straight on flop
    engine.community_cards = [Card(Rank.QUEEN, Suit.HEARTS), Card(Rank.JACK, Suit.DIAMONDS), Card(Rank.TEN, Suit.CLUBS)]
    _act(engine, "p2", "check")
    _act(engine, "p1", "check")
    
    # Turn
    engine.community_cards.append(Card(Rank.TWO, Suit.SPADES))
    _act(engine, "p2", "check")
    _act(engine, "p1", "check")
    
    # River
    engine.community_cards.append(Card(Rank.THREE, Suit.HEARTS))
    _act(engine, "p2", "check")
    _act(engine, "p1", "check")
    
    assert engine.state == GameState.FINISHED
    assert len(engine.winners) == 2
    
    # Alice (p1) was BB (20). Bob (p2) was SB (10->20). Pot=40. Split=20 each.
    # Alice chips: 1000 - 20 + 20 = 1000.
    # Bob chips: 1000 - 20 + 20 = 1000.
    assert engine.players[0].chips == 1000
    assert engine.players[1].chips == 1000

def test_scenario_5_multi_player_folding():
    """
    Scenario 5: 3-Player Round
    - Alice (Dealer), Bob (SB), Carol (BB)
    """
    engine = PokerEngine()
    engine.add_player("p1", "Alice", 1000)
    engine.add_player("p2", "Bob", 1000)
    engine.add_player("p3", "Carol", 1000)
    engine.dealer_idx = 2 # Carol dealer
    engine.start_hand() # Alice (p1) becomes dealer. Bob (p2) SB, Carol (p3) BB.
    
    # Action starts at (dealer+3)%3 = (0+3)%3 = 0 (Alice/Dealer/Button acts first pre-flop?)
    # Wait, (0+3)%3 = 0. UTG acts first. In 3p, Button is effectively UTG?
    # Usually fold/call/raise from Button.
    _act(engine, "p1", "raise", 60)
    _act(engine, "p2", "call") # Bob (SB) calls
    _act(engine, "p3", "fold") # Carol (BB) folds
    
    assert engine.state == GameState.FLOP
    
    # Post-flop: SB acts first. Bob (p2) is SB.
    _act(engine, "p2", "check")
    # Alice (p1) acts next
    _act(engine, "p1", "raise", 100)
    _act(engine, "p2", "fold")
    
    assert engine.state == GameState.FINISHED
    assert engine.winners == ["p1"]
    # Alice wins
    # Carol (p3) lost 20 (BB) -> 980
    # Bob (p2) lost 60 (pf call) -> 940
    # Alice (p1) chips: 1000 - 160 + (60+60+20) = 1080. 
    # Wait, pot = 60(A)+60(B)+20(C) = 140. Alice bet 100 more on flop.
    # Total pot = 140 + 100 = 240.
    # Alice put in 60(pf) + 100(f) = 160.
    assert engine.players[0].chips == 1080
    assert engine.players[1].chips == 940
    assert engine.players[2].chips == 980

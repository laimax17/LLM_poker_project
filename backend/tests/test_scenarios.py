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
    engine.community_cards[-1] = Card(Rank.TWO, Suit.SPADES)
    _act(engine, "p2", "check")
    _act(engine, "p1", "check")
    
    # River
    engine.community_cards[-1] = Card(Rank.THREE, Suit.HEARTS)
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


def test_scenario_6_walk_fold_to_bb():
    """
    Scenario 6: Walk — Fold to Big Blind (3-player)
    - UTG (Alice/Button) and SB (Bob) both fold pre-flop.
    - BB (Carol) wins the blinds without seeing a flop.

    Setup: dealer_idx_before=2 → dealer=0(Alice), SB=1(Bob,10), BB=2(Carol,20)
    First to act pre-flop: (0+3)%3=0 = Alice (Button/UTG)
    """
    engine = PokerEngine()
    engine.add_player("p1", "Alice", 1000)
    engine.add_player("p2", "Bob", 1000)
    engine.add_player("p3", "Carol", 1000)
    engine.dealer_idx = 2  # rotation → dealer=0 (Alice)
    engine.start_hand()

    # Alice (Button/UTG) folds
    _act(engine, "p1", "fold")
    # Bob (SB) folds → only Carol remains
    _act(engine, "p2", "fold")

    assert engine.state == GameState.FINISHED
    assert engine.winners == ["p3"]
    assert engine.winning_hand_rank == "Opponents Folded"

    # Alice: 1000 (never put chips in)
    # Bob:   1000 - 10 (SB) = 990
    # Carol: 1000 - 20 (BB) + 30 (pot) = 1010
    assert engine.players[0].chips == 1000
    assert engine.players[1].chips == 990
    assert engine.players[2].chips == 1010
    assert sum(p.chips for p in engine.players) == 3000


def test_scenario_7_three_bet_pot_to_showdown():
    """
    Scenario 7: 3-Bet Pot to Showdown (2-player)
    - Bob (SB) raises, Alice (BB) 3-bets, Bob calls.
    - Alice continuation-bets flop and turn, checks river.
    - Alice wins with top pair (Pair of Aces) vs Bob's Pair of Queens.

    Setup: dealer=0(Alice=BB), SB=1(Bob).
    Chips in: Alice=500 (BB180+flop120+turn200), Bob=500 → Pot=1000.
    """
    engine = _setup_game([("p1", "Alice", 1000), ("p2", "Bob", 1000)], 1)
    engine.players[0].hand = [Card(Rank.ACE, Suit.SPADES), Card(Rank.KING, Suit.DIAMONDS)]
    engine.players[1].hand = [Card(Rank.QUEEN, Suit.HEARTS), Card(Rank.QUEEN, Suit.DIAMONDS)]

    # Pre-flop: Bob (SB) raises, Alice 3-bets, Bob calls
    _act(engine, "p2", "raise", 60)   # Bob raise to 60
    _act(engine, "p1", "raise", 180)  # Alice 3-bet to 180
    _act(engine, "p2", "call")        # Bob calls 180 → pot=360

    assert engine.state == GameState.FLOP

    # Inject flop: Ace-high dry board
    engine.community_cards = [
        Card(Rank.ACE, Suit.CLUBS),
        Card(Rank.SEVEN, Suit.SPADES),
        Card(Rank.TWO, Suit.DIAMONDS),
    ]

    # Flop: Bob (SB) checks, Alice c-bets 120
    _act(engine, "p2", "check")
    _act(engine, "p1", "raise", 120)  # Alice bets 120
    _act(engine, "p2", "call")        # Bob calls → pot=600

    assert engine.state == GameState.TURN

    # Inject turn: blank
    engine.community_cards[-1] = Card(Rank.NINE, Suit.CLUBS)

    # Turn: Bob checks, Alice fires again 200
    _act(engine, "p2", "check")
    _act(engine, "p1", "raise", 200)
    _act(engine, "p2", "call")        # pot=1000

    assert engine.state == GameState.RIVER

    # Inject river: blank
    engine.community_cards[-1] = Card(Rank.FIVE, Suit.HEARTS)

    # River: both check → showdown
    _act(engine, "p2", "check")
    _act(engine, "p1", "check")

    assert engine.state == GameState.FINISHED
    assert engine.winners == ["p1"]
    assert engine.winning_hand_rank == "Pair"

    # Alice in: 180(pf) + 120(flop) + 200(turn) = 500
    # Bob in:   180(pf) + 120(flop) + 200(turn) = 500  → pot=1000
    assert engine.players[0].chips == 1500
    assert engine.players[1].chips == 500
    assert sum(p.chips for p in engine.players) == 2000


def test_scenario_8_check_raise_on_flop():
    """
    Scenario 8: Check-Raise on the Flop (2-player)
    - Bob (SB) donk-bets flop; Alice (BB) check-raises.
    - Alice holds top set (KKK) and wins at showdown.

    Flop check-raise: Bob bets 20 → Alice raises to 60 (min: current_bet+min_raise=20+20=40 ✓).
    """
    engine = _setup_game([("p1", "Alice", 1000), ("p2", "Bob", 1000)], 1)
    engine.players[0].hand = [Card(Rank.KING, Suit.SPADES), Card(Rank.KING, Suit.DIAMONDS)]
    engine.players[1].hand = [Card(Rank.ACE, Suit.HEARTS), Card(Rank.JACK, Suit.HEARTS)]

    # Pre-flop: Bob calls, Alice checks → pot=40
    _act(engine, "p2", "call")
    _act(engine, "p1", "check")
    assert engine.state == GameState.FLOP

    # Inject flop: King-high board with flush draw for Bob
    engine.community_cards = [
        Card(Rank.KING, Suit.HEARTS),
        Card(Rank.TEN, Suit.HEARTS),
        Card(Rank.TWO, Suit.CLUBS),
    ]

    # Flop: Bob leads for 20, Alice check-raises to 60
    _act(engine, "p2", "raise", 20)   # Bob bets 20 into 0 → current_bet=20, rc=1
    _act(engine, "p1", "raise", 60)   # Alice check-raises to 60 (≥20+20=40 ✓), rc=2
    _act(engine, "p2", "call")        # Bob calls 40 more → pot=160

    assert engine.state == GameState.TURN

    # Inject blank turn and river
    engine.community_cards[-1] = Card(Rank.EIGHT, Suit.DIAMONDS)
    _act(engine, "p2", "check")
    _act(engine, "p1", "check")
    assert engine.state == GameState.RIVER

    engine.community_cards[-1] = Card(Rank.THREE, Suit.SPADES)
    _act(engine, "p2", "check")
    _act(engine, "p1", "check")

    assert engine.state == GameState.FINISHED
    assert engine.winners == ["p1"]
    assert engine.winning_hand_rank == "Three Of A Kind"

    # Alice in: 20(BB) + 60(flop check-raise) = 80
    # Bob in:   20(pf call) + 60(flop: 20 bet + 40 call) = 80  → pot=160
    assert engine.players[0].chips == 1080
    assert engine.players[1].chips == 920
    assert sum(p.chips for p in engine.players) == 2000


def test_scenario_9_double_barrel_bluff_loses():
    """
    Scenario 9: Double Barrel Bluff Loses at Showdown (2-player)
    - Alice (BB) bluffs flop and turn with 7-2 offsuit (the worst hand).
    - Alice checks river and loses to Bob's Ace-high.
    - Verifies the aggressor's chips are correctly deducted even when they lose.
    """
    engine = _setup_game([("p1", "Alice", 1000), ("p2", "Bob", 1000)], 1)
    engine.players[0].hand = [Card(Rank.SEVEN, Suit.SPADES), Card(Rank.TWO, Suit.DIAMONDS)]
    engine.players[1].hand = [Card(Rank.ACE, Suit.HEARTS), Card(Rank.KING, Suit.DIAMONDS)]

    # Pre-flop: Bob calls, Alice checks → pot=40
    _act(engine, "p2", "call")
    _act(engine, "p1", "check")
    assert engine.state == GameState.FLOP

    # Inject dry flop (no help for either player)
    engine.community_cards = [
        Card(Rank.NINE, Suit.CLUBS),
        Card(Rank.SIX, Suit.HEARTS),
        Card(Rank.THREE, Suit.SPADES),
    ]

    # Flop: Bob checks, Alice bluffs 30
    _act(engine, "p2", "check")
    _act(engine, "p1", "raise", 30)
    _act(engine, "p2", "call")   # pot=100

    assert engine.state == GameState.TURN
    engine.community_cards[-1] = Card(Rank.JACK, Suit.DIAMONDS)

    # Turn: Bob checks, Alice double-barrels 60
    _act(engine, "p2", "check")
    _act(engine, "p1", "raise", 60)
    _act(engine, "p2", "call")   # pot=220

    assert engine.state == GameState.RIVER
    engine.community_cards[-1] = Card(Rank.TEN, Suit.SPADES)

    # River: Bob checks, Alice gives up
    _act(engine, "p2", "check")
    _act(engine, "p1", "check")

    assert engine.state == GameState.FINISHED
    assert engine.winners == ["p2"]
    assert engine.winning_hand_rank == "High Card"

    # Alice in: 20(BB) + 30(flop) + 60(turn) = 110
    # Bob in:   20(pf) + 30(flop) + 60(turn) = 110 → pot=220
    assert engine.players[0].chips == 890
    assert engine.players[1].chips == 1110
    assert sum(p.chips for p in engine.players) == 2000


def test_scenario_10_allin_preflop_aa_vs_kk():
    """
    Scenario 10: Pre-flop All-in — AA vs KK (Classic Cooler)
    - SB 3-bets, BB re-raises all-in, SB calls.
    - Board is controlled via deck stacking (both all-in → engine auto-runs).
    - AA holds on a dry board; Alice wins all 2000 chips.
    """
    engine = _setup_game([("p1", "Alice", 1000), ("p2", "Bob", 1000)], 1)
    engine.players[0].hand = [Card(Rank.ACE, Suit.CLUBS), Card(Rank.ACE, Suit.DIAMONDS)]
    engine.players[1].hand = [Card(Rank.KING, Suit.HEARTS), Card(Rank.KING, Suit.SPADES)]

    # Pre-flop sequence: Bob raises, Alice 3-bets, Bob shoves, Alice calls
    _act(engine, "p2", "raise", 60)    # Bob raise to 60, rc=1
    _act(engine, "p1", "raise", 180)   # Alice 3-bet to 180, rc=2
    _act(engine, "p2", "allin")        # Bob all-in (1000 total), rc=3

    # Stack the deck before Alice's call so the auto-run deals known cards:
    # deck.pop() yields from end → store reversed: [river, turn, flop3, flop2, flop1]
    # Board: flop=5c 8d 2h, turn=Jc, river=3s
    engine.deck = [
        Card(Rank.THREE, Suit.SPADES),   # river (popped last)
        Card(Rank.JACK, Suit.CLUBS),     # turn
        Card(Rank.TWO, Suit.HEARTS),     # flop card 3
        Card(Rank.EIGHT, Suit.DIAMONDS), # flop card 2
        Card(Rank.FIVE, Suit.CLUBS),     # flop card 1 (popped first)
    ]

    _act(engine, "p1", "call")  # Alice calls → both all-in → auto-run to showdown

    assert engine.state == GameState.FINISHED
    assert engine.winners == ["p1"]
    assert engine.winning_hand_rank == "Pair"
    assert len(engine.community_cards) == 5

    # Alice wins entire pot (2000 chips)
    assert engine.players[0].chips == 2000
    assert engine.players[1].chips == 0
    assert sum(p.chips for p in engine.players) == 2000


def test_scenario_11_multi_hand_sequence():
    """
    Scenario 11: Three Consecutive Hands (2-player)
    Verifies: dealer rotation, chip carry-over, total-chip conservation.

    Hand 1: dealer=0(Alice=BB), SB=Bob.  Alice AA beats Bob KK. +40 to Alice.
    Hand 2: dealer=1(Bob=BB),   SB=Alice. Bob QQ beats Alice 32. +40 to Bob.
    Hand 3: dealer=0(Alice=BB), SB=Bob.  Alice JJ beats Bob TT. +40 to Alice.

    Each hand: SB calls, BB checks, everyone checks to showdown.
    Deck stacking controls the board (pattern B).
    """
    engine = PokerEngine()
    engine.add_player("p1", "Alice", 1000)
    engine.add_player("p2", "Bob", 1000)
    engine.dealer_idx = 1  # rotation → dealer=0 (Alice)

    # ── Hand 1: dealer=0(Alice=BB), SB=1(Bob) ──────────────────────────────
    engine.start_hand()
    assert engine.dealer_idx == 0

    engine.players[0].hand = [Card(Rank.ACE, Suit.SPADES), Card(Rank.ACE, Suit.HEARTS)]
    engine.players[1].hand = [Card(Rank.KING, Suit.SPADES), Card(Rank.KING, Suit.HEARTS)]
    # board: flop=2c 3d 5h, turn=7s, river=9c
    engine.deck = [
        Card(Rank.NINE, Suit.CLUBS),
        Card(Rank.SEVEN, Suit.SPADES),
        Card(Rank.FIVE, Suit.HEARTS),
        Card(Rank.THREE, Suit.DIAMONDS),
        Card(Rank.TWO, Suit.CLUBS),
    ]

    _act(engine, "p2", "call")   # Bob (SB) calls
    _act(engine, "p1", "check")  # Alice (BB) checks → FLOP
    _act(engine, "p2", "check"); _act(engine, "p1", "check")  # flop
    _act(engine, "p2", "check"); _act(engine, "p1", "check")  # turn
    _act(engine, "p2", "check"); _act(engine, "p1", "check")  # river

    assert engine.state == GameState.FINISHED
    assert engine.winners == ["p1"]  # AA > KK
    assert engine.players[0].chips == 1020  # 980 + pot(40)
    assert engine.players[1].chips == 980
    assert sum(p.chips for p in engine.players) == 2000

    # ── Hand 2: dealer=1(Bob=BB), SB=0(Alice) ──────────────────────────────
    engine.start_hand()
    assert engine.dealer_idx == 1

    engine.players[0].hand = [Card(Rank.TWO, Suit.SPADES), Card(Rank.THREE, Suit.SPADES)]
    engine.players[1].hand = [Card(Rank.QUEEN, Suit.HEARTS), Card(Rank.QUEEN, Suit.DIAMONDS)]
    # board: flop=4c 7h 9d, turn=Jc, river=5s
    engine.deck = [
        Card(Rank.FIVE, Suit.SPADES),
        Card(Rank.JACK, Suit.CLUBS),
        Card(Rank.NINE, Suit.DIAMONDS),
        Card(Rank.SEVEN, Suit.HEARTS),
        Card(Rank.FOUR, Suit.CLUBS),
    ]

    _act(engine, "p1", "call")   # Alice (SB) calls
    _act(engine, "p2", "check")  # Bob (BB) checks → FLOP
    _act(engine, "p1", "check"); _act(engine, "p2", "check")  # flop
    _act(engine, "p1", "check"); _act(engine, "p2", "check")  # turn
    _act(engine, "p1", "check"); _act(engine, "p2", "check")  # river

    assert engine.state == GameState.FINISHED
    assert engine.winners == ["p2"]  # QQ > 32
    assert engine.players[0].chips == 1000  # 1020 - 20(SB+call) + 0 = 1000
    assert engine.players[1].chips == 1000  # 960 + 40 = 1000
    assert sum(p.chips for p in engine.players) == 2000

    # ── Hand 3: dealer=0(Alice=BB), SB=1(Bob) ──────────────────────────────
    engine.start_hand()
    assert engine.dealer_idx == 0

    engine.players[0].hand = [Card(Rank.JACK, Suit.HEARTS), Card(Rank.JACK, Suit.DIAMONDS)]
    engine.players[1].hand = [Card(Rank.TEN, Suit.HEARTS), Card(Rank.TEN, Suit.DIAMONDS)]
    # board: flop=2h Kd 8s, turn=5h, river=3c
    engine.deck = [
        Card(Rank.THREE, Suit.CLUBS),
        Card(Rank.FIVE, Suit.HEARTS),
        Card(Rank.EIGHT, Suit.SPADES),
        Card(Rank.KING, Suit.DIAMONDS),
        Card(Rank.TWO, Suit.HEARTS),
    ]

    _act(engine, "p2", "call")   # Bob (SB) calls
    _act(engine, "p1", "check")  # Alice (BB) checks → FLOP
    _act(engine, "p2", "check"); _act(engine, "p1", "check")  # flop
    _act(engine, "p2", "check"); _act(engine, "p1", "check")  # turn
    _act(engine, "p2", "check"); _act(engine, "p1", "check")  # river

    assert engine.state == GameState.FINISHED
    assert engine.winners == ["p1"]  # JJ > TT
    assert engine.players[0].chips == 1020
    assert engine.players[1].chips == 980
    assert sum(p.chips for p in engine.players) == 2000


def test_scenario_12_player_elimination_across_hands():
    """
    Scenario 12: Player Elimination Across Two Hands (3-player)
    - Hand 1: Short-stacked Bob (100 chips) goes all-in pre-flop and loses to Carol.
              Bob is eliminated (chips=0).
    - Hand 2: Game continues with just Alice and Carol (Bob is inactive).
              Verifies Bob.is_active==False and chip total is conserved.
    """
    engine = PokerEngine()
    engine.add_player("p1", "Alice", 1000)
    engine.add_player("p2", "Bob", 100)
    engine.add_player("p3", "Carol", 1000)
    engine.dealer_idx = 2  # rotation → dealer=0 (Alice)

    # ── Hand 1: dealer=0(Alice), SB=1(Bob,10), BB=2(Carol,20) ─────────────
    engine.start_hand()

    engine.players[1].hand = [Card(Rank.SEVEN, Suit.HEARTS), Card(Rank.TWO, Suit.DIAMONDS)]
    engine.players[2].hand = [Card(Rank.ACE, Suit.HEARTS), Card(Rank.KING, Suit.SPADES)]
    # Board: flop=Ac 7c 5d, turn=8h, river=3c
    engine.deck = [
        Card(Rank.THREE, Suit.CLUBS),
        Card(Rank.EIGHT, Suit.HEARTS),
        Card(Rank.FIVE, Suit.DIAMONDS),
        Card(Rank.SEVEN, Suit.CLUBS),
        Card(Rank.ACE, Suit.CLUBS),
    ]

    _act(engine, "p1", "fold")    # Alice folds (UTG/Button)
    _act(engine, "p2", "allin")   # Bob all-in (90 more, total=100), rc=1
    _act(engine, "p3", "call")    # Carol calls → active non-all-in=[Carol] → auto-run

    assert engine.state == GameState.FINISHED
    assert engine.winners == ["p3"]  # PairA beats Pair7

    bob = engine.players[1]
    carol = engine.players[2]
    assert bob.chips == 0
    assert carol.chips == 1100  # 900 + pot(200)
    assert sum(p.chips for p in engine.players) == 2100

    # ── Hand 2: dealer rotates to 1 (Bob, inactive) ────────────────────────
    engine.start_hand()
    assert engine.dealer_idx == 1

    bob = engine.players[1]
    assert bob.is_active is False  # Bob has 0 chips → sits out

    # 2 active players: Carol (SB) and Alice (BB)
    # SB=(1+1)%3=2(Carol), BB=(1+2)%3=0(Alice)
    alice = engine.players[0]
    carol = engine.players[2]

    alice.hand = [Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.KING, Suit.DIAMONDS)]
    carol.hand = [Card(Rank.TWO, Suit.SPADES), Card(Rank.THREE, Suit.SPADES)]
    engine.deck = [
        Card(Rank.FIVE, Suit.SPADES),
        Card(Rank.JACK, Suit.CLUBS),
        Card(Rank.NINE, Suit.DIAMONDS),
        Card(Rank.SEVEN, Suit.HEARTS),
        Card(Rank.FOUR, Suit.CLUBS),
    ]

    # First active non-all-in player after dealer(Bob,inactive) is Carol (SB)
    _act(engine, "p3", "call")   # Carol (SB) calls
    _act(engine, "p1", "check")  # Alice (BB) checks → FLOP
    _act(engine, "p3", "check"); _act(engine, "p1", "check")  # flop
    _act(engine, "p3", "check"); _act(engine, "p1", "check")  # turn
    _act(engine, "p3", "check"); _act(engine, "p1", "check")  # river

    assert engine.state == GameState.FINISHED
    assert engine.winners == ["p1"]  # AK > 32

    assert engine.players[1].chips == 0   # Bob still out
    assert sum(p.chips for p in engine.players) == 2100


def test_scenario_13_multiway_pot_to_showdown():
    """
    Scenario 13: Multi-way Pot to Showdown (3-player)
    - All three players see the flop.
    - Carol folds on the flop after Alice bets.
    - Alice and Bob go to showdown; Alice wins with Pair of Aces vs Pair of Jacks.

    Chip breakdown:
      Alice in: 20(pf) + 40(flop) = 60  →  wins pot=140 → 1080
      Bob in:   20(pf) + 40(flop) = 60  →  940
      Carol in: 20(BB)             = 20  →  980
    """
    engine = PokerEngine()
    engine.add_player("p1", "Alice", 1000)
    engine.add_player("p2", "Bob", 1000)
    engine.add_player("p3", "Carol", 1000)
    engine.dealer_idx = 2  # rotation → dealer=0(Alice), SB=1(Bob), BB=2(Carol)
    engine.start_hand()

    engine.players[0].hand = [Card(Rank.ACE, Suit.HEARTS), Card(Rank.KING, Suit.HEARTS)]
    engine.players[1].hand = [Card(Rank.JACK, Suit.DIAMONDS), Card(Rank.JACK, Suit.CLUBS)]
    engine.players[2].hand = [Card(Rank.NINE, Suit.SPADES), Card(Rank.EIGHT, Suit.SPADES)]

    # Pre-flop: Alice (Button) calls, Bob (SB) calls, Carol (BB) checks → pot=60
    _act(engine, "p1", "call")   # Alice calls 20
    _act(engine, "p2", "call")   # Bob calls 10 more
    _act(engine, "p3", "check")  # Carol checks (BB option)
    assert engine.state == GameState.FLOP

    # Inject flop: Ace on board
    engine.community_cards = [
        Card(Rank.ACE, Suit.CLUBS),
        Card(Rank.SEVEN, Suit.DIAMONDS),
        Card(Rank.TWO, Suit.HEARTS),
    ]

    # Flop: Bob (SB) checks, Carol checks, Alice bets 40
    _act(engine, "p2", "check")
    _act(engine, "p3", "check")
    _act(engine, "p1", "raise", 40)   # Alice bets 40, rc=1
    _act(engine, "p2", "call")        # Bob calls
    _act(engine, "p3", "fold")        # Carol folds → active=[Alice,Bob]

    assert engine.state == GameState.TURN

    # Inject turn and river (blanks)
    engine.community_cards[-1] = Card(Rank.TEN, Suit.SPADES)
    _act(engine, "p2", "check")
    _act(engine, "p1", "check")
    assert engine.state == GameState.RIVER

    engine.community_cards[-1] = Card(Rank.FOUR, Suit.CLUBS)
    _act(engine, "p2", "check")
    _act(engine, "p1", "check")

    assert engine.state == GameState.FINISHED
    assert engine.winners == ["p1"]
    assert engine.winning_hand_rank == "Pair"  # Pair Aces > Pair Jacks

    assert engine.players[0].chips == 1080
    assert engine.players[1].chips == 940
    assert engine.players[2].chips == 980
    assert sum(p.chips for p in engine.players) == 3000


def test_scenario_14_min_raise_sizing_update():
    """
    Scenario 14: Min-raise Sizing Update (2-player)
    Verifies that min_raise stays at 20 for equal-increment raises, then
    updates to 100 when a raise increment exceeds the current min_raise,
    and resets to big_blind (20) at the start of the next street.
    """
    engine = _setup_game([("p1", "Alice", 2000), ("p2", "Bob", 2000)], 1)
    # dealer=0(Alice=BB), SB=1(Bob), current_bet=20, min_raise=20

    # Each raise resets opponent's has_acted → street doesn't advance until a call

    # Raise 1: Bob to 40 (diff=40-20=20, not > 20 → min_raise stays 20)
    _act(engine, "p2", "raise", 40)
    assert engine.current_bet == 40
    assert engine.min_raise == 20
    assert engine.raise_count == 1

    # Raise 2: Alice to 60 (diff=60-40=20 → min_raise stays 20)
    _act(engine, "p1", "raise", 60)
    assert engine.current_bet == 60
    assert engine.min_raise == 20
    assert engine.raise_count == 2

    # Raise 3: Bob to 80 (diff=80-60=20 → min_raise stays 20)
    _act(engine, "p2", "raise", 80)
    assert engine.current_bet == 80
    assert engine.min_raise == 20
    assert engine.raise_count == 3

    # Raise 4: Alice to 180 — big jump (+100 above 80; diff=100 > 20 → min_raise=100)
    _act(engine, "p1", "raise", 180)
    assert engine.current_bet == 180
    assert engine.min_raise == 100
    assert engine.raise_count == 4  # cap reached

    # Bob calls (cannot raise again; cap=4)
    _act(engine, "p2", "call")
    assert engine.state == GameState.FLOP

    # After street transition: raise_count and min_raise reset
    assert engine.raise_count == 0
    assert engine.min_raise == 20  # reset to big_blind

    # Inject flop, turn, river and check through to showdown
    engine.players[0].hand = [Card(Rank.ACE, Suit.SPADES), Card(Rank.ACE, Suit.HEARTS)]
    engine.players[1].hand = [Card(Rank.SEVEN, Suit.SPADES), Card(Rank.TWO, Suit.CLUBS)]
    engine.community_cards = [
        Card(Rank.FOUR, Suit.CLUBS),
        Card(Rank.EIGHT, Suit.DIAMONDS),
        Card(Rank.THREE, Suit.HEARTS),
    ]
    _act(engine, "p2", "check"); _act(engine, "p1", "check")  # flop
    engine.community_cards[-1] = Card(Rank.KING, Suit.SPADES)
    _act(engine, "p2", "check"); _act(engine, "p1", "check")  # turn
    engine.community_cards[-1] = Card(Rank.SIX, Suit.HEARTS)
    _act(engine, "p2", "check"); _act(engine, "p1", "check")  # river

    assert engine.state == GameState.FINISHED
    assert engine.winners == ["p1"]  # AA wins

    # Both put in 180 pre-flop → pot=360. Alice wins.
    assert engine.players[0].chips == 2180  # 2000-180+360
    assert engine.players[1].chips == 1820  # 2000-180
    assert sum(p.chips for p in engine.players) == 4000


def test_scenario_15_river_value_bet_called():
    """
    Scenario 15: River Value Bet Gets Called (2-player)
    - Quiet hand (check/check) through flop and turn.
    - Alice bets 50 on the river (value), Bob calls.
    - Alice wins with Pair of Queens vs Bob's Jack-high.

    Chip breakdown:
      Alice in: 20(BB) + 50(river) = 70  →  wins pot=140 → 1070
      Bob in:   20(pf) + 50(river) = 70  →  930
    """
    engine = _setup_game([("p1", "Alice", 1000), ("p2", "Bob", 1000)], 1)
    engine.players[0].hand = [Card(Rank.QUEEN, Suit.HEARTS), Card(Rank.QUEEN, Suit.SPADES)]
    engine.players[1].hand = [Card(Rank.JACK, Suit.HEARTS), Card(Rank.TEN, Suit.DIAMONDS)]

    # Pre-flop: Bob calls, Alice checks → pot=40
    _act(engine, "p2", "call")
    _act(engine, "p1", "check")
    assert engine.state == GameState.FLOP

    # Inject flop: no help for either player
    engine.community_cards = [
        Card(Rank.FOUR, Suit.CLUBS),
        Card(Rank.SEVEN, Suit.DIAMONDS),
        Card(Rank.TWO, Suit.SPADES),
    ]
    _act(engine, "p2", "check")
    _act(engine, "p1", "check")
    assert engine.state == GameState.TURN

    engine.community_cards[-1] = Card(Rank.NINE, Suit.HEARTS)
    _act(engine, "p2", "check")
    _act(engine, "p1", "check")
    assert engine.state == GameState.RIVER

    engine.community_cards[-1] = Card(Rank.THREE, Suit.CLUBS)

    # River: Bob checks, Alice fires a value bet of 50
    _act(engine, "p2", "check")
    _act(engine, "p1", "raise", 50)  # Alice bets 50
    _act(engine, "p2", "call")       # Bob calls → pot=140

    assert engine.state == GameState.FINISHED
    assert engine.winners == ["p1"]
    assert engine.winning_hand_rank == "Pair"  # Pair Queens > Jack-high

    assert engine.players[0].chips == 1070
    assert engine.players[1].chips == 930
    assert sum(p.chips for p in engine.players) == 2000

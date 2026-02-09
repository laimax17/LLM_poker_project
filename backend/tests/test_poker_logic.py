import pytest
import sys
# Ensure backend module is importable
sys.path.append('.')

from backend.src.engine import PokerEngine, Card, Rank, Suit, HandEvaluator, HandRank, Player, GameState

# --- Hand Evaluator Tests ---

def test_high_card():
    cards = [
        Card(Rank.ACE, Suit.HEARTS),
        Card(Rank.TEN, Suit.CLUBS),
        Card(Rank.EIGHT, Suit.DIAMONDS),
        Card(Rank.FIVE, Suit.SPADES),
        Card(Rank.TWO, Suit.HEARTS)
    ]
    rank, kickers = HandEvaluator.evaluate(cards)
    assert rank == HandRank.HIGH_CARD
    assert kickers[0] == 14

def test_pair():
    cards = [
        Card(Rank.ACE, Suit.HEARTS),
        Card(Rank.ACE, Suit.CLUBS),
        Card(Rank.EIGHT, Suit.DIAMONDS),
        Card(Rank.FIVE, Suit.SPADES),
        Card(Rank.TWO, Suit.HEARTS)
    ]
    rank, kickers = HandEvaluator.evaluate(cards)
    assert rank == HandRank.PAIR
    assert kickers[0] == 14 # Pair rank

def test_two_pair():
    cards = [
        Card(Rank.ACE, Suit.HEARTS),
        Card(Rank.ACE, Suit.CLUBS),
        Card(Rank.KING, Suit.DIAMONDS),
        Card(Rank.KING, Suit.SPADES),
        Card(Rank.TWO, Suit.HEARTS)
    ]
    rank, kickers = HandEvaluator.evaluate(cards)
    assert rank == HandRank.TWO_PAIR
    assert kickers[0] == 14 # Pair 1
    assert kickers[1] == 13 # Pair 2

def test_three_of_a_kind():
    cards = [
        Card(Rank.ACE, Suit.HEARTS),
        Card(Rank.ACE, Suit.CLUBS),
        Card(Rank.ACE, Suit.DIAMONDS),
        Card(Rank.KING, Suit.SPADES),
        Card(Rank.TWO, Suit.HEARTS)
    ]
    rank, kickers = HandEvaluator.evaluate(cards)
    assert rank == HandRank.THREE_OF_A_KIND
    assert kickers[0] == 14

def test_straight():
    cards = [
        Card(Rank.FIVE, Suit.HEARTS),
        Card(Rank.FOUR, Suit.CLUBS),
        Card(Rank.THREE, Suit.DIAMONDS),
        Card(Rank.TWO, Suit.SPADES),
        Card(Rank.ACE, Suit.HEARTS)
    ]
    # Wheel A-5
    rank, kickers = HandEvaluator.evaluate(cards)
    assert rank == HandRank.STRAIGHT
    assert kickers == [5, 4, 3, 2, 1]

def test_flush():
    cards = [
        Card(Rank.ACE, Suit.HEARTS),
        Card(Rank.TEN, Suit.HEARTS),
        Card(Rank.EIGHT, Suit.HEARTS),
        Card(Rank.FIVE, Suit.HEARTS),
        Card(Rank.TWO, Suit.HEARTS)
    ]
    rank, kickers = HandEvaluator.evaluate(cards)
    assert rank == HandRank.FLUSH

def test_full_house():
    cards = [
        Card(Rank.ACE, Suit.HEARTS),
        Card(Rank.ACE, Suit.CLUBS),
        Card(Rank.ACE, Suit.DIAMONDS),
        Card(Rank.KING, Suit.SPADES),
        Card(Rank.KING, Suit.HEARTS)
    ]
    rank, kickers = HandEvaluator.evaluate(cards)
    assert rank == HandRank.FULL_HOUSE

def test_four_of_a_kind():
    cards = [
        Card(Rank.ACE, Suit.HEARTS),
        Card(Rank.ACE, Suit.CLUBS),
        Card(Rank.ACE, Suit.DIAMONDS),
        Card(Rank.ACE, Suit.SPADES),
        Card(Rank.KING, Suit.HEARTS)
    ]
    rank, kickers = HandEvaluator.evaluate(cards)
    assert rank == HandRank.FOUR_OF_A_KIND

def test_straight_flush():
    cards = [
        Card(Rank.FIVE, Suit.HEARTS),
        Card(Rank.FOUR, Suit.HEARTS),
        Card(Rank.THREE, Suit.HEARTS),
        Card(Rank.TWO, Suit.HEARTS),
        Card(Rank.ACE, Suit.HEARTS)
    ]
    rank, kickers = HandEvaluator.evaluate(cards)
    assert rank == HandRank.STRAIGHT_FLUSH

def test_royal_flush():
    cards = [
        Card(Rank.ACE, Suit.HEARTS),
        Card(Rank.KING, Suit.HEARTS),
        Card(Rank.QUEEN, Suit.HEARTS),
        Card(Rank.JACK, Suit.HEARTS),
        Card(Rank.TEN, Suit.HEARTS)
    ]
    rank, kickers = HandEvaluator.evaluate(cards)
    assert rank == HandRank.ROYAL_FLUSH

# --- Game Engine Tests ---

def test_game_flow():
    engine = PokerEngine()
    engine.add_player("p1", "Player 1", 1000)
    engine.add_player("p2", "Player 2", 1000)
    
    engine.start_hand()
    assert engine.state == GameState.PREFLOP
    assert engine.pot == 30 # 10 SB + 20 BB
    
    current_p = engine.players[engine.current_player_idx]
    
    # P2 Call (SB acts first in 2-player generic logic?)
    # In my logic engine.current_player_idx = (dealer+3)%N.
    # N=2. Dealer=0. SB=1. BB=0.
    # (0+3)%2 = 1. P2 Acts first.
    
    # P2 Call 10 to match 20
    engine.player_action(current_p.id, "call")
    assert engine.pot == 40
    
    # P1 (BB) Check
    current_p = engine.players[engine.current_player_idx]
    engine.player_action(current_p.id, "check")
    
    assert engine.state == GameState.FLOP
    assert len(engine.community_cards) == 3

def test_betting_logic():
    engine = PokerEngine()
    engine.add_player("p1", "Player 1", 1000)
    engine.add_player("p2", "Player 2", 1000)
    engine.start_hand()
    
    p = engine.players[engine.current_player_idx] # P2
    
    # Raise to 60 total
    engine.player_action(p.id, "raise", 60)
    assert engine.current_bet == 60
    # Pot: 10(sb) + 20(bb) + (60 - 10) = 80
    assert engine.pot == 80
    
    # Next player fold
    next_p = engine.players[engine.current_player_idx]
    engine.player_action(next_p.id, "fold")
    
    assert engine.state == GameState.FINISHED
    winner = [x for x in engine.players if x.id == p.id][0]
    # Chips: 1000 - 60 + 80 = 1020
    assert winner.chips == 1020

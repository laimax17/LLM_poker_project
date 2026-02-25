"""
Comprehensive tests for the PokerEngine and HandEvaluator.

Covers:
- Hand evaluation (all 10 hand ranks)
- Betting mechanics (raise, call, check, fold, all-in)
- Raise cap enforcement (max 4 raises per street)
- Full-game flow (PREFLOP → FLOP → TURN → RIVER → FINISHED)
- BB option pre-flop
- Dealer rotation across hands
- Split pot
- Multi-player scenarios
- Edge cases (undercall all-in, chip exhaustion)
"""
import pytest
import sys
sys.path.append('.')

from backend.src.engine import (
    PokerEngine, Card, Rank, Suit,
    HandEvaluator, HandRank, Player, GameState,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _engine_2p(chips: int = 1000) -> PokerEngine:
    """Return a fresh 2-player engine with start_hand() called."""
    e = PokerEngine()
    e.add_player("p1", "Alice", chips)
    e.add_player("p2", "Bob", chips)
    e.start_hand()
    return e


def _act(engine: PokerEngine, action: str, amount: int = 0) -> None:
    """Perform an action for whichever player's turn it is."""
    p = engine.players[engine.current_player_idx]
    engine.player_action(p.id, action, amount)


def _run_to_showdown(engine: PokerEngine) -> None:
    """Check/call through every remaining street until the hand finishes."""
    while engine.state not in (GameState.FINISHED, GameState.SHOWDOWN):
        p = engine.players[engine.current_player_idx]
        needed = engine.current_bet - p.current_bet
        if needed == 0:
            engine.player_action(p.id, "check")
        else:
            engine.player_action(p.id, "call")


# ---------------------------------------------------------------------------
# Hand Evaluator Tests
# ---------------------------------------------------------------------------

def test_high_card():
    cards = [
        Card(Rank.ACE, Suit.HEARTS), Card(Rank.TEN, Suit.CLUBS),
        Card(Rank.EIGHT, Suit.DIAMONDS), Card(Rank.FIVE, Suit.SPADES),
        Card(Rank.TWO, Suit.HEARTS),
    ]
    rank, kickers = HandEvaluator.evaluate(cards)
    assert rank == HandRank.HIGH_CARD
    assert kickers[0] == 14


def test_pair():
    cards = [
        Card(Rank.ACE, Suit.HEARTS), Card(Rank.ACE, Suit.CLUBS),
        Card(Rank.EIGHT, Suit.DIAMONDS), Card(Rank.FIVE, Suit.SPADES),
        Card(Rank.TWO, Suit.HEARTS),
    ]
    rank, kickers = HandEvaluator.evaluate(cards)
    assert rank == HandRank.PAIR
    assert kickers[0] == 14


def test_two_pair():
    cards = [
        Card(Rank.ACE, Suit.HEARTS), Card(Rank.ACE, Suit.CLUBS),
        Card(Rank.KING, Suit.DIAMONDS), Card(Rank.KING, Suit.SPADES),
        Card(Rank.TWO, Suit.HEARTS),
    ]
    rank, kickers = HandEvaluator.evaluate(cards)
    assert rank == HandRank.TWO_PAIR
    assert kickers[0] == 14
    assert kickers[1] == 13


def test_three_of_a_kind():
    cards = [
        Card(Rank.ACE, Suit.HEARTS), Card(Rank.ACE, Suit.CLUBS),
        Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.KING, Suit.SPADES),
        Card(Rank.TWO, Suit.HEARTS),
    ]
    rank, kickers = HandEvaluator.evaluate(cards)
    assert rank == HandRank.THREE_OF_A_KIND
    assert kickers[0] == 14


def test_straight():
    cards = [
        Card(Rank.FIVE, Suit.HEARTS), Card(Rank.FOUR, Suit.CLUBS),
        Card(Rank.THREE, Suit.DIAMONDS), Card(Rank.TWO, Suit.SPADES),
        Card(Rank.ACE, Suit.HEARTS),
    ]
    rank, kickers = HandEvaluator.evaluate(cards)
    assert rank == HandRank.STRAIGHT
    assert kickers == [5, 4, 3, 2, 1]  # Wheel A-5


def test_flush():
    cards = [
        Card(Rank.ACE, Suit.HEARTS), Card(Rank.TEN, Suit.HEARTS),
        Card(Rank.EIGHT, Suit.HEARTS), Card(Rank.FIVE, Suit.HEARTS),
        Card(Rank.TWO, Suit.HEARTS),
    ]
    rank, _ = HandEvaluator.evaluate(cards)
    assert rank == HandRank.FLUSH


def test_full_house():
    cards = [
        Card(Rank.ACE, Suit.HEARTS), Card(Rank.ACE, Suit.CLUBS),
        Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.KING, Suit.SPADES),
        Card(Rank.KING, Suit.HEARTS),
    ]
    rank, _ = HandEvaluator.evaluate(cards)
    assert rank == HandRank.FULL_HOUSE


def test_four_of_a_kind():
    cards = [
        Card(Rank.ACE, Suit.HEARTS), Card(Rank.ACE, Suit.CLUBS),
        Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.ACE, Suit.SPADES),
        Card(Rank.KING, Suit.HEARTS),
    ]
    rank, _ = HandEvaluator.evaluate(cards)
    assert rank == HandRank.FOUR_OF_A_KIND


def test_straight_flush():
    cards = [
        Card(Rank.FIVE, Suit.HEARTS), Card(Rank.FOUR, Suit.HEARTS),
        Card(Rank.THREE, Suit.HEARTS), Card(Rank.TWO, Suit.HEARTS),
        Card(Rank.ACE, Suit.HEARTS),
    ]
    rank, _ = HandEvaluator.evaluate(cards)
    assert rank == HandRank.STRAIGHT_FLUSH


def test_royal_flush():
    cards = [
        Card(Rank.ACE, Suit.HEARTS), Card(Rank.KING, Suit.HEARTS),
        Card(Rank.QUEEN, Suit.HEARTS), Card(Rank.JACK, Suit.HEARTS),
        Card(Rank.TEN, Suit.HEARTS),
    ]
    rank, _ = HandEvaluator.evaluate(cards)
    assert rank == HandRank.ROYAL_FLUSH


# ---------------------------------------------------------------------------
# Basic Game Engine Tests (original, now with corrected assertions)
# ---------------------------------------------------------------------------

def test_game_flow():
    """SB calls, BB checks → should advance to FLOP."""
    engine = _engine_2p()
    assert engine.state == GameState.PREFLOP
    assert engine.pot == 30  # 10 SB + 20 BB

    # With 2 players: dealer_idx=1, SB=player[0], BB=player[1]
    # current_player_idx = (1+3)%2 = 0 → SB acts first pre-flop
    _act(engine, "call")       # SB calls → pot=40
    assert engine.pot == 40

    _act(engine, "check")      # BB checks (BB option) → FLOP
    assert engine.state == GameState.FLOP
    assert len(engine.community_cards) == 3


def test_betting_logic():
    """Raise then fold → winner gets pot, state == FINISHED."""
    engine = _engine_2p()
    p = engine.players[engine.current_player_idx]

    engine.player_action(p.id, "raise", 60)
    assert engine.current_bet == 60
    assert engine.pot == 80  # 10 SB + 20 BB + (60-10) added by raiser

    next_p = engine.players[engine.current_player_idx]
    engine.player_action(next_p.id, "fold")

    assert engine.state == GameState.FINISHED
    winner = next(x for x in engine.players if x.id == p.id)
    assert winner.chips == 1020  # 1000 - 60 + 80


# ---------------------------------------------------------------------------
# Full-Game Flow Tests
# ---------------------------------------------------------------------------

def test_full_hand_all_streets():
    """Both players call/check through all 4 streets → FINISHED, 5 community cards."""
    engine = _engine_2p()
    _run_to_showdown(engine)

    assert engine.state == GameState.FINISHED
    assert len(engine.community_cards) == 5
    # Pot must be distributed: total chips conserved
    total_chips = sum(p.chips for p in engine.players)
    assert total_chips == 2000


def test_state_progression():
    """Verify exact state sequence: PREFLOP→FLOP→TURN→RIVER→FINISHED."""
    engine = _engine_2p()
    assert engine.state == GameState.PREFLOP

    _act(engine, "call")
    _act(engine, "check")
    assert engine.state == GameState.FLOP

    _act(engine, "check")
    _act(engine, "check")
    assert engine.state == GameState.TURN

    _act(engine, "check")
    _act(engine, "check")
    assert engine.state == GameState.RIVER

    _act(engine, "check")
    _act(engine, "check")
    assert engine.state == GameState.FINISHED


def test_chips_conserved_after_full_hand():
    """Total chips across all players always equals starting total."""
    engine = _engine_2p(chips=500)
    _run_to_showdown(engine)
    assert sum(p.chips for p in engine.players) == 1000


# ---------------------------------------------------------------------------
# Pre-flop BB Option Tests
# ---------------------------------------------------------------------------

def test_preflop_bb_option_check():
    """When SB just calls, BB gets to act (option). BB check ends the round."""
    engine = _engine_2p()
    # SB acts first (current_player_idx after start_hand)
    sb = engine.players[engine.current_player_idx]
    engine.player_action(sb.id, "call")

    # BB still needs to act (has_acted=False)
    assert engine.state == GameState.PREFLOP
    bb = engine.players[engine.current_player_idx]
    assert bb.id != sb.id  # different player
    engine.player_action(bb.id, "check")
    assert engine.state == GameState.FLOP


def test_preflop_bb_option_raise():
    """BB raises after SB call → SB must call again before street ends."""
    engine = _engine_2p()
    sb = engine.players[engine.current_player_idx]
    engine.player_action(sb.id, "call")  # SB calls to 20

    bb = engine.players[engine.current_player_idx]
    engine.player_action(bb.id, "raise", 60)  # BB raises to 60

    # SB must still act
    assert engine.state == GameState.PREFLOP
    assert engine.players[engine.current_player_idx].id == sb.id
    engine.player_action(sb.id, "call")  # SB calls
    assert engine.state == GameState.FLOP


# ---------------------------------------------------------------------------
# Raise Cap Tests
# ---------------------------------------------------------------------------

def test_raise_cap_enforced():
    """After max_raises_per_street raises, further raises are rejected."""
    engine = _engine_2p(chips=5000)
    assert engine.max_raises_per_street == 4

    # Alternate raises between SB and BB (each raise resets opponent's
    # has_acted, so the street never advances until someone calls).

    # Raise 1: SB raises to 40
    p = engine.players[engine.current_player_idx]
    engine.player_action(p.id, "raise", 40)
    assert engine.raise_count == 1

    # Raise 2: BB re-raises to 60
    p = engine.players[engine.current_player_idx]
    engine.player_action(p.id, "raise", 60)
    assert engine.raise_count == 2

    # Raise 3: SB re-raises to 80
    p = engine.players[engine.current_player_idx]
    engine.player_action(p.id, "raise", 80)
    assert engine.raise_count == 3

    # Raise 4: BB re-raises to 100 (cap reached)
    p = engine.players[engine.current_player_idx]
    engine.player_action(p.id, "raise", 100)
    assert engine.raise_count == 4

    # Raise 5: SB tries to raise again -> must be rejected
    p = engine.players[engine.current_player_idx]
    with pytest.raises(ValueError, match="Raise cap"):
        engine.player_action(p.id, "raise", 120)


def test_raise_cap_simple():
    """Direct test: 4 raises in a row hit the cap."""
    engine = PokerEngine()
    engine.max_raises_per_street = 2  # Lower cap for easy testing
    engine.add_player("p1", "Alice", 5000)
    engine.add_player("p2", "Bob", 5000)
    engine.start_hand()

    # Raise 1
    p = engine.players[engine.current_player_idx]
    engine.player_action(p.id, "raise", 60)
    assert engine.raise_count == 1

    # The other player re-raises (raise 2 → cap reached)
    p2 = engine.players[engine.current_player_idx]
    engine.player_action(p2.id, "raise", 120)
    assert engine.raise_count == 2

    # Now the original player tries to raise again → should fail
    p = engine.players[engine.current_player_idx]
    with pytest.raises(ValueError, match="Raise cap"):
        engine.player_action(p.id, "raise", 200)


def test_raise_cap_resets_each_street():
    """raise_count resets to 0 at the start of each new street."""
    engine = PokerEngine()
    engine.max_raises_per_street = 2
    engine.add_player("p1", "Alice", 5000)
    engine.add_player("p2", "Bob", 5000)
    engine.start_hand()

    # Use both raises pre-flop
    p = engine.players[engine.current_player_idx]
    engine.player_action(p.id, "raise", 60)
    p2 = engine.players[engine.current_player_idx]
    engine.player_action(p2.id, "raise", 120)
    assert engine.raise_count == 2

    # Call to end the pre-flop street
    p = engine.players[engine.current_player_idx]
    engine.player_action(p.id, "call")
    assert engine.state == GameState.FLOP

    # raise_count should be reset
    assert engine.raise_count == 0

    # Should be able to raise again on the flop
    p = engine.players[engine.current_player_idx]
    engine.player_action(p.id, "raise", engine.current_bet + engine.min_raise)
    assert engine.raise_count == 1


# ---------------------------------------------------------------------------
# All-in Tests
# ---------------------------------------------------------------------------

def test_all_in_call():
    """Player goes all-in, opponent calls → chips conserved, game finishes."""
    engine = _engine_2p(chips=200)

    p = engine.players[engine.current_player_idx]
    engine.player_action(p.id, "allin")

    p2 = engine.players[engine.current_player_idx]
    engine.player_action(p2.id, "call")

    assert engine.state == GameState.FINISHED
    total = sum(p.chips for p in engine.players)
    assert total == 400


def test_all_in_counts_as_raise():
    """All-in that exceeds current_bet increments raise_count."""
    engine = _engine_2p(chips=1000)
    assert engine.raise_count == 0

    p = engine.players[engine.current_player_idx]
    # Player goes all-in with more than current_bet → should count as raise
    engine.player_action(p.id, "allin")
    assert engine.raise_count == 1


def test_allin_as_undercall():
    """Player with fewer chips can still go all-in (treated as partial call)."""
    engine = PokerEngine()
    engine.add_player("p1", "Rich", 1000)
    engine.add_player("p2", "Short", 15)  # Less than big blind
    engine.start_hand()

    # The short-stacked player should be forced all-in for the blinds already
    short = next(p for p in engine.players if p.name == "Short")
    # If short stack is already all-in from blinds, game should still work
    if short.is_all_in:
        # Game continues, resolve
        _run_to_showdown(engine)
        assert engine.state == GameState.FINISHED
    else:
        # Short stack goes all-in
        if engine.players[engine.current_player_idx].id == short.id:
            engine.player_action(short.id, "allin")
        _run_to_showdown(engine)
        assert engine.state == GameState.FINISHED


# ---------------------------------------------------------------------------
# Multi-player Tests
# ---------------------------------------------------------------------------

def test_fold_wins_pot():
    """Three-player game: two fold, last player wins the pot."""
    engine = PokerEngine()
    engine.add_player("p1", "Alice", 1000)
    engine.add_player("p2", "Bob", 1000)
    engine.add_player("p3", "Carol", 1000)
    engine.start_hand()

    initial_pot = engine.pot  # SB + BB

    # First two players fold
    _act(engine, "fold")
    _act(engine, "fold")

    assert engine.state == GameState.FINISHED
    assert len(engine.winners) == 1
    winner = next(p for p in engine.players if p.id == engine.winners[0])
    # Winner gained the pot
    assert winner.chips == 1000 + initial_pot - winner.current_bet


def test_three_player_full_hand():
    """Three players check/call all the way to showdown."""
    engine = PokerEngine()
    engine.add_player("p1", "Alice", 1000)
    engine.add_player("p2", "Bob", 1000)
    engine.add_player("p3", "Carol", 1000)
    engine.start_hand()

    _run_to_showdown(engine)

    assert engine.state == GameState.FINISHED
    assert len(engine.community_cards) == 5
    total = sum(p.chips for p in engine.players)
    assert total == 3000


# ---------------------------------------------------------------------------
# Split Pot Test
# ---------------------------------------------------------------------------

def test_split_pot():
    """Both players have equal best hand → pot splits evenly."""
    engine = PokerEngine()
    engine.add_player("p1", "Alice", 1000)
    engine.add_player("p2", "Bob", 1000)
    engine.start_hand()

    # Manually inject identical hole cards (both get A♠ K♠ — same ranks, diff suits)
    # and a community board that makes a straight for both
    engine.players[0].hand = [
        Card(Rank.ACE, Suit.HEARTS), Card(Rank.KING, Suit.HEARTS),
    ]
    engine.players[1].hand = [
        Card(Rank.ACE, Suit.SPADES), Card(Rank.KING, Suit.SPADES),
    ]
    engine.community_cards = [
        Card(Rank.QUEEN, Suit.CLUBS), Card(Rank.JACK, Suit.DIAMONDS),
        Card(Rank.TEN, Suit.CLUBS), Card(Rank.TWO, Suit.DIAMONDS),
        Card(Rank.THREE, Suit.HEARTS),
    ]
    # Simulate entering the River street cleanly
    engine.state = GameState.RIVER
    engine.current_bet = 0
    engine.raise_count = 0
    for p in engine.players:
        p.current_bet = 0
        p.has_acted = False
    engine.current_player_idx = (engine.dealer_idx + 1) % len(engine.players)

    # Both check → triggers _resolve_hand
    _act(engine, "check")
    _act(engine, "check")

    assert engine.state == GameState.FINISHED
    assert len(engine.winners) == 2
    # Total chips must be conserved (pot split between both winners)
    total = sum(p.chips for p in engine.players)
    assert total == 2000
    # Each winner received exactly half the pot (30 // 2 = 15)
    half_pot = engine.pot // 2  # pot is 0 after distribution, check via chip totals
    p1 = next(p for p in engine.players if p.id == "p1")
    p2 = next(p for p in engine.players if p.id == "p2")
    # p1 was SB (-10), p2 was BB (-20); each gets 15 back → p1=1005, p2=995
    assert p1.chips == 1005
    assert p2.chips == 995


# ---------------------------------------------------------------------------
# Dealer Rotation Tests
# ---------------------------------------------------------------------------

def test_dealer_rotation():
    """After the first hand, dealer_idx advances and SB/BB positions shift."""
    engine = PokerEngine()
    engine.add_player("p1", "Alice", 1000)
    engine.add_player("p2", "Bob", 1000)

    engine.start_hand()
    first_dealer = engine.dealer_idx

    # Finish the hand
    _run_to_showdown(engine)

    engine.start_hand()
    second_dealer = engine.dealer_idx

    assert second_dealer != first_dealer
    assert second_dealer == (first_dealer + 1) % 2


# ---------------------------------------------------------------------------
# Validation / Error Tests
# ---------------------------------------------------------------------------

def test_cannot_raise_more_than_chips():
    """Raise amount exceeding player chips raises ValueError."""
    engine = _engine_2p(chips=100)
    p = engine.players[engine.current_player_idx]
    with pytest.raises(ValueError, match="Not enough chips"):
        engine.player_action(p.id, "raise", 9999)


def test_min_raise_enforced():
    """Raise below current_bet + min_raise raises ValueError."""
    engine = _engine_2p(chips=1000)
    p = engine.players[engine.current_player_idx]
    # current_bet=20, min_raise=20 → must raise to at least 40
    with pytest.raises(ValueError, match="Raise too small"):
        engine.player_action(p.id, "raise", 25)


def test_cannot_check_when_bet_outstanding():
    """Player cannot check when there is a bet they need to call."""
    engine = _engine_2p()
    # SB is already in debt (posted 10, current_bet is 20) — try to check
    sb = engine.players[engine.current_player_idx]
    with pytest.raises(ValueError, match="Cannot check"):
        engine.player_action(sb.id, "check")


def test_wrong_player_turn_raises():
    """Acting out of turn raises ValueError."""
    engine = _engine_2p()
    wrong_idx = (engine.current_player_idx + 1) % 2
    wrong = engine.players[wrong_idx]
    with pytest.raises(ValueError, match="Not your turn"):
        engine.player_action(wrong.id, "call")


# ---------------------------------------------------------------------------
# Public State Tests
# ---------------------------------------------------------------------------

def test_public_state_exposes_raise_fields():
    """get_public_game_state includes raise_count, max_raises_per_street, can_raise."""
    engine = _engine_2p()
    state = engine.get_public_game_state("p1")
    assert "raise_count" in state
    assert "max_raises_per_street" in state
    assert "can_raise" in state
    assert state["raise_count"] == 0
    assert state["max_raises_per_street"] == 4
    assert state["can_raise"] is True


def test_public_state_hides_opponents_hand():
    """Observer only sees own hole cards; opponent's hand is masked."""
    engine = _engine_2p()
    state = engine.get_public_game_state("p1")
    p1_data = next(p for p in state["players"] if p["id"] == "p1")
    p2_data = next(p for p in state["players"] if p["id"] == "p2")
    # p1 sees their own cards
    assert all(c is not None for c in p1_data["hand"])
    # p1 cannot see p2's cards
    assert all(c is None for c in p2_data["hand"])


def test_public_state_reveals_hands_at_showdown():
    """At a real showdown (both players go to river), all active hands are visible."""
    engine = _engine_2p()
    # Play through all streets to force a real showdown
    # PREFLOP: p1 calls BB, p2 checks
    engine.player_action(engine.players[engine.current_player_idx].id, "call")
    engine.player_action(engine.players[engine.current_player_idx].id, "check")
    # FLOP: both check
    engine.player_action(engine.players[engine.current_player_idx].id, "check")
    engine.player_action(engine.players[engine.current_player_idx].id, "check")
    # TURN: both check
    engine.player_action(engine.players[engine.current_player_idx].id, "check")
    engine.player_action(engine.players[engine.current_player_idx].id, "check")
    # RIVER: both check → triggers showdown
    engine.player_action(engine.players[engine.current_player_idx].id, "check")
    engine.player_action(engine.players[engine.current_player_idx].id, "check")

    assert engine.state == GameState.FINISHED
    assert engine.winning_hand_rank != "Opponents Folded"
    assert len(engine.winners) > 0

    state = engine.get_public_game_state("p1")
    p1_data = next(p for p in state["players"] if p["id"] == "p1")
    p2_data = next(p for p in state["players"] if p["id"] == "p2")
    # Both players are active (neither folded), so both hands must be visible
    assert all(c is not None for c in p1_data["hand"]), "p1 hand should be visible at showdown"
    assert all(c is not None for c in p2_data["hand"]), "p2 hand should be visible at showdown"


def test_public_state_hides_hands_when_win_by_fold():
    """When all opponents fold, the winner's hole cards are NOT revealed."""
    engine = _engine_2p()
    # p1 folds immediately → p2 wins by fold
    engine.player_action(engine.players[engine.current_player_idx].id, "fold")

    assert engine.state == GameState.FINISHED
    assert engine.winning_hand_rank == "Opponents Folded"

    state = engine.get_public_game_state("p1")
    p2_data = next(p for p in state["players"] if p["id"] == "p2")
    # p2 won by fold; their cards must remain hidden from p1's perspective
    assert all(c is None for c in p2_data["hand"]), "winner's cards should stay hidden when win by fold"

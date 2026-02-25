import random
from typing import List, Dict, Optional, Tuple, Set
from enum import Enum
from dataclasses import dataclass, field
from .schemas import Suit, Rank

@dataclass
class Card:
    rank: Rank
    suit: Suit

    def to_dict(self):
        return {"rank": self.rank.value, "suit": self.suit.value}

@dataclass
class Player:
    id: str
    name: str
    chips: int
    hand: List[Card] = field(default_factory=list)
    is_active: bool = True
    current_bet: int = 0
    is_all_in: bool = False
    has_acted: bool = False 

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "chips": self.chips,
            "hand": [c.to_dict() for c in self.hand],
            "is_active": self.is_active,
            "current_bet": self.current_bet,
            "is_all_in": self.is_all_in,
            "has_acted": self.has_acted
        }

class HandRank(Enum):
    HIGH_CARD = 1
    PAIR = 2
    TWO_PAIR = 3
    THREE_OF_A_KIND = 4
    STRAIGHT = 5
    FLUSH = 6
    FULL_HOUSE = 7
    FOUR_OF_A_KIND = 8
    STRAIGHT_FLUSH = 9
    ROYAL_FLUSH = 10

class HandEvaluator:
    @staticmethod
    def evaluate(cards: List[Card]) -> Tuple[HandRank, List[int]]:
        if len(cards) < 5:
            return HandRank.HIGH_CARD, []
            
        import itertools
        best_rank = HandRank.HIGH_CARD
        best_tiebreakers = []

        for combo in itertools.combinations(cards, 5):
            combo_list = sorted(list(combo), key=lambda c: c.rank.value, reverse=True)
            rank, tiebreakers = HandEvaluator._evaluate_five(combo_list)
            
            if rank.value > best_rank.value:
                best_rank = rank
                best_tiebreakers = tiebreakers
            elif rank.value == best_rank.value:
                if tiebreakers > best_tiebreakers:
                    best_tiebreakers = tiebreakers
                    
        return best_rank, best_tiebreakers

    @staticmethod
    def _evaluate_five(cards: List[Card]) -> Tuple[HandRank, List[int]]:
        ranks = [c.rank.value for c in cards]
        suits = [c.suit for c in cards]
        
        is_flush = len(set(suits)) == 1
        
        is_straight = False
        # Sort ranks for straight check
        sorted_ranks = sorted(list(set(ranks)), reverse=True)
        # We need to check if ANY 5 consecutive ranks exist? 
        # No, we already have exactly 5 cards in this helper.
        # Just check if max - min == 4 and unique
        if len(set(ranks)) == 5 and (ranks[0] - ranks[4] == 4):
            is_straight = True
        # Wheel check: A, 5, 4, 3, 2 -> 14, 5, 4, 3, 2
        if ranks == [14, 5, 4, 3, 2]:
            is_straight = True
            ranks = [5, 4, 3, 2, 1]

        if is_straight and is_flush:
            if ranks[0] == 14 and ranks[4] == 10:
                return HandRank.ROYAL_FLUSH, []
            return HandRank.STRAIGHT_FLUSH, ranks
        
        counts = {r: ranks.count(r) for r in set(ranks)}
        sorted_counts = sorted(counts.items(), key=lambda x: (x[1], x[0]), reverse=True)
        
        if sorted_counts[0][1] == 4:
            return HandRank.FOUR_OF_A_KIND, [sorted_counts[0][0], sorted_counts[1][0]]
            
        if sorted_counts[0][1] == 3 and sorted_counts[1][1] == 2:
            return HandRank.FULL_HOUSE, [sorted_counts[0][0], sorted_counts[1][0]]
        
        if is_flush:
            return HandRank.FLUSH, ranks
        
        if is_straight:
            return HandRank.STRAIGHT, ranks
            
        if sorted_counts[0][1] == 3:
            return HandRank.THREE_OF_A_KIND, [sorted_counts[0][0]] + [x for x in ranks if x != sorted_counts[0][0]]
            
        if sorted_counts[0][1] == 2 and sorted_counts[1][1] == 2:
            return HandRank.TWO_PAIR, [sorted_counts[0][0], sorted_counts[1][0]] + [x for x in ranks if x not in [sorted_counts[0][0], sorted_counts[1][0]]]
            
        if sorted_counts[0][1] == 2:
            return HandRank.PAIR, [sorted_counts[0][0]] + [x for x in ranks if x != sorted_counts[0][0]]
            
        return HandRank.HIGH_CARD, ranks

class GameState(Enum):
    PREFLOP = "PREFLOP"
    FLOP = "FLOP"
    TURN = "TURN"
    RIVER = "RIVER"
    SHOWDOWN = "SHOWDOWN"
    FINISHED = "FINISHED"

class PokerEngine:
    def __init__(self):
        self.players: List[Player] = []
        self.community_cards: List[Card] = []
        self.deck: List[Card] = []
        self.pot: int = 0
        self.current_bet: int = 0
        self.state: GameState = GameState.PREFLOP
        self.dealer_idx: int = 0
        self.current_player_idx: int = 0
        self.small_blind: int = 10
        self.big_blind: int = 20
        self.min_raise: int = 20
        self.raise_count: int = 0
        self.max_raises_per_street: int = 4

    def reset_deck(self):
        self.deck = [Card(r, s) for r in Rank for s in Suit]
        random.shuffle(self.deck)

    def add_player(self, player_id: str, name: str, chips: int):
        self.players.append(Player(player_id, name, chips))

    def start_hand(self):
        # Rotate dealer
        self.dealer_idx = (self.dealer_idx + 1) % len(self.players)
        
        self.reset_deck()
        self.community_cards = []
        self.pot = 0
        self.current_bet = 0
        self.min_raise = self.big_blind
        self.state = GameState.PREFLOP
        self.winners = []
        self.winning_hand_rank = ""
        
        for p in self.players:
            p.hand = []
            p.is_active = True if p.chips > 0 else False
            p.current_bet = 0
            p.is_all_in = False
            p.has_acted = False
        
        active_count = sum(1 for p in self.players if p.is_active)
        if active_count < 2:
            raise ValueError("Not enough players")

        for _ in range(2):
            for p in self.players:
                if p.is_active:
                    p.hand.append(self.deck.pop())

        sb_idx = (self.dealer_idx + 1) % len(self.players)
        bb_idx = (self.dealer_idx + 2) % len(self.players)
        
        self._place_bet_logic(self.players[sb_idx], self.small_blind)
        self._place_bet_logic(self.players[bb_idx], self.big_blind)
        
        self.current_player_idx = (self.dealer_idx + 3) % len(self.players)
        # Skip all-in or inactive players
        steps = 0
        while not (self.players[self.current_player_idx].is_active and not self.players[self.current_player_idx].is_all_in) and steps < len(self.players):
            self.current_player_idx = (self.current_player_idx + 1) % len(self.players)
            steps += 1

        self.current_bet = self.big_blind
        self.raise_count = 0

    def _place_bet_logic(self, player: Player, amount: int):
        actual = min(player.chips, amount)
        player.chips -= actual
        player.current_bet += actual
        self.pot += actual
        if player.chips == 0:
            player.is_all_in = True
        
        if player.current_bet > self.current_bet:
            diff = player.current_bet - self.current_bet
            if diff > self.min_raise:
                self.min_raise = diff
            self.current_bet = player.current_bet

    def player_action(self, player_id: str, action: str, amount: int = 0):
        p = next((x for x in self.players if x.id == player_id), None)
        if not p:
            raise ValueError("Player not found")
        if p != self.players[self.current_player_idx]:
             raise ValueError(f"Not your turn. Current: {self.players[self.current_player_idx].name}")

        if action == "fold":
            p.is_active = False
        elif action == "check":
            if p.current_bet < self.current_bet:
                raise ValueError("Cannot check, must call")
        elif action == "call":
            needed = self.current_bet - p.current_bet
            self._place_bet_logic(p, needed)
        elif action == "raise":
            if self.raise_count >= self.max_raises_per_street:
                raise ValueError(f"Raise cap reached ({self.max_raises_per_street} raises per street)")
            if amount < self.current_bet + self.min_raise:
                 if amount < p.chips + p.current_bet:
                     raise ValueError(f"Raise too small. Min total: {self.current_bet + self.min_raise}")

            added = amount - p.current_bet
            if added > p.chips:
                raise ValueError("Not enough chips")
            self._place_bet_logic(p, added)
            self.raise_count += 1
        elif action == "allin":
            if p.chips + p.current_bet > self.current_bet:
                self.raise_count += 1
            self._place_bet_logic(p, p.chips)

        p.has_acted = True
        
        if action == "raise" or action == "allin":
             for other in self.players:
                 if other != p and other.is_active and not other.is_all_in:
                     other.has_acted = False

        self._advance_turn()

    def _advance_turn(self):
        active_players = [p for p in self.players if p.is_active and not p.is_all_in]
        
        actives_total = [p for p in self.players if p.is_active]
        if len(actives_total) == 1:
            self._resolve_hand(actives_total[0])
            return

        bets_match = all(p.current_bet == self.current_bet for p in active_players)
        all_acted = all(p.has_acted for p in active_players)
        
        if (bets_match and all_acted) or len(active_players) == 0:
            self._next_street()
        else:
            steps = 0
            while steps <= len(self.players):
                self.current_player_idx = (self.current_player_idx + 1) % len(self.players)
                next_p = self.players[self.current_player_idx]
                if next_p.is_active and not next_p.is_all_in:
                    break
                steps += 1

    def _next_street(self):
        self.current_bet = 0
        self.min_raise = self.big_blind
        self.raise_count = 0
        for p in self.players:
            p.current_bet = 0
            p.has_acted = False
            
        self.current_player_idx = (self.dealer_idx + 1) % len(self.players)
        while not (self.players[self.current_player_idx].is_active and not self.players[self.current_player_idx].is_all_in):
             self.current_player_idx = (self.current_player_idx + 1) % len(self.players)
             if all(p.is_all_in or not p.is_active for p in self.players):
                 break

        if self.state == GameState.PREFLOP:
            self.state = GameState.FLOP
            self.community_cards.extend([self.deck.pop() for _ in range(3)])
        elif self.state == GameState.FLOP:
            self.state = GameState.TURN
            self.community_cards.append(self.deck.pop())
        elif self.state == GameState.TURN:
            self.state = GameState.RIVER
            self.community_cards.append(self.deck.pop())
        elif self.state == GameState.RIVER:
            self._resolve_hand()
            return
            
        # Helper to check if we just run it out
        count_actions_needed = sum(1 for p in self.players if p.is_active and not p.is_all_in)
        if count_actions_needed < 2:
             while self.state != GameState.FINISHED:
                  self._next_street()
                  if self.state == GameState.FINISHED: 
                       return

    def _resolve_hand(self, winner_by_fold: Optional[Player] = None):
        self.state = GameState.SHOWDOWN
        self.winners = []
        self.winning_hand_rank = ""

        if winner_by_fold:
            winner_by_fold.chips += self.pot
            self.winners = [winner_by_fold.id]
            self.winning_hand_rank = "Opponents Folded"
        else:
            active_players = [p for p in self.players if p.is_active]
            results = []
            for p in active_players:
                rank, tiebreakers = HandEvaluator.evaluate(p.hand + self.community_cards)
                results.append((p, rank, tiebreakers))
            
            results.sort(key=lambda x: (x[1].value, x[2]), reverse=True)
            
            if not results:
                return 

            best = results[0]
            winners_list = [r[0] for r in results if r[1].value == best[1].value and r[2] == best[2]]
            
            split = self.pot // len(winners_list)
            rem = self.pot % len(winners_list)
            
            for w in winners_list:
                w.chips += split
            winners_list[0].chips += rem
            
            self.winners = [w.id for w in winners_list]
            self.winning_hand_rank = best[1].name.replace("_", " ").title()

        self.state = GameState.FINISHED

    def get_public_game_state(self, observer_id: str):
        # Base state
        state = {
            "state": self.state.value,
            "pot": self.pot,
            "community_cards": [c.to_dict() for c in self.community_cards],
            "players": [],
            "current_player_idx": self.current_player_idx,
            "current_bet": self.current_bet,
            "min_raise": self.min_raise,
            "raise_count": self.raise_count,
            "max_raises_per_street": self.max_raises_per_street,
            "can_raise": self.raise_count < self.max_raises_per_street,
            "winners": getattr(self, "winners", []),
            "winning_hand": getattr(self, "winning_hand_rank", "")
        }

        # Reveal hands at a real showdown: multiple players went to showdown (not fold-out)
        is_actual_showdown = (
            self.state in (GameState.SHOWDOWN, GameState.FINISHED)
            and getattr(self, 'winning_hand_rank', '') not in ('', 'Opponents Folded')
            and bool(getattr(self, 'winners', []))
        )

        for p in self.players:
            p_data = p.to_dict()
            # Mask hand if not the observer, unless this is a real showdown and the player
            # stayed in (didn't fold) — folded players' cards are never revealed.
            if p.id != observer_id and not (is_actual_showdown and p.is_active):
                p_data["hand"] = [None] * len(p.hand)
            state["players"].append(p_data)
            
        return state

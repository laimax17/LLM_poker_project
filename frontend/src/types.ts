export type Suit = "Hearts" | "Diamonds" | "Clubs" | "Spades";

export interface Card {
  rank: number;
  suit: Suit;
}

export interface Player {
  id: string;
  name: string;
  chips: number;
  hand: Card[];
  is_active: boolean;
  current_bet: number;
  is_all_in: boolean;
  has_acted: boolean;
  is_dealer: boolean;
}

export interface GameState {
  state: string;
  pot: number;
  community_cards: Card[];
  players: Player[];
  current_player_idx: number;
  current_bet: number;
  min_raise: number;
  winners: string[];
  winning_hand: string;
}

export interface AIThought {
  thought: string;
  chat: string;
}

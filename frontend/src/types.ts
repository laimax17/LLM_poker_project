export type Suit = "Hearts" | "Diamonds" | "Clubs" | "Spades";

export interface Card {
  rank: number;
  suit: Suit;
}

export interface Player {
  id: string;
  name: string;
  chips: number;
  hand: (Card | null)[];
  is_active: boolean;
  current_bet: number;
  is_all_in: boolean;
  has_acted: boolean;
  is_dealer: boolean;
  is_turn: boolean;
}

export type GameStreet = 'PREFLOP' | 'FLOP' | 'TURN' | 'RIVER' | 'SHOWDOWN' | 'FINISHED';

export interface GameState {
  state: GameStreet;
  pot: number;
  community_cards: Card[];
  players: Player[];
  current_player_idx: number;
  current_bet: number;
  min_raise: number;
  winners: string[];
  winning_hand: string;
  can_raise: boolean;
  raise_count: number;
  max_raises_per_street: number;
}

export type LLMEngine = 'rule-based' | 'gto' | 'ollama' | 'qwen-plus' | 'qwen-max';

export interface LLMConfig {
  engine: LLMEngine;
  model: string;
  status: 'online' | 'offline' | 'loading';
}

export interface AICoachStat {
  label: string;
  value: string;
  quality: 'good' | 'bad' | 'hot' | 'neutral';
}

export interface AICoachAdvice {
  recommendation: 'FOLD' | 'CALL' | 'CHECK' | 'RAISE';
  recommendedAmount?: number;
  body: string;
  stats: AICoachStat[];
}

export interface BotThought {
  player_id: string;
  thought: string;
  chat: string;
  fading?: boolean;
}

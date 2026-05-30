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
  winning_cards: Card[];
  can_raise: boolean;
  raise_count: number;
  max_raises_per_street: number;
}

// 'rule-based' | 'gto' | 'ollama' | provider id ('openrouter' | 'deepseek' | ...)
export type LLMEngine = string;

export interface LLMConfig {
  engine: LLMEngine;
  model: string;
  status: 'online' | 'offline' | 'loading';
}

export interface ProviderInfo {
  id: string;
  label: string;
  available: boolean;
  defaultModel: string;
}

export interface ModelInfo {
  id: string;
  label: string;
  provider: string;
}

export interface ModelsRegistry {
  providers: ProviderInfo[];
  models: ModelInfo[];
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

// ─── Learning Mode ──────────────────────────────────────────────────────────

export interface LiveHint {
  recommendation: 'FOLD' | 'CALL' | 'CHECK' | 'RAISE';
  recommendedAmount?: number | null;
  stats: AICoachStat[];
  isPreflop: boolean;
}

export type DecisionGrade = 'correct' | 'marginal' | 'mistake';

export interface DecisionRecord {
  street: string;
  handStr: string;
  boardStr: string;
  pot: number;
  toCall: number;
  recommendation: string;
  recommendedAmount?: number | null;
  position: string;
  action: string;
  amount: number;
  grade: DecisionGrade;
  explanation: string;
}

export interface HandReview {
  handNumber: number;
  netChips: number;
  decisions: DecisionRecord[];
}

export interface SessionLeak {
  text: string;
  severity: 'good' | 'bad' | 'neutral';
}

export interface SessionStats {
  handsPlayed: number;
  vpip: number;
  pfr: number;
  aggressionFactor: number;
  netChips: number;
  correct: number;
  marginal: number;
  mistake: number;
  leaks: SessionLeak[];
}

export interface BotThought {
  player_id: string;
  thought: string;
  chat: string;
  fading?: boolean;
}

// ─── Tournament ───────────────────────────────────────────────────────────────

export interface GameSetupConfig {
  num_opponents: number;
  starting_stack: number;
  blind_speed: 'turbo' | 'normal' | 'slow';
  difficulty: 'easy' | 'normal' | 'hard';
}

export interface TournamentState {
  active: boolean;
  level: number;
  smallBlind: number;
  bigBlind: number;
  ante: number;
  handsUntilNextLevel: number;
  playersRemaining: number;
  totalPlayers: number;
  yourPlace: number;
  handCount: number;
}

export interface StandingEntry {
  id: string;
  name: string;
  place: number;
  chips: number;
}

export interface EliminationEvent {
  id: string;
  name: string;
  place: number;
}

export interface AllInEquityPlayer {
  id: string;
  name: string;
  equity: number;
}

export interface AllInEquity {
  street: string;
  board: Card[];
  players: AllInEquityPlayer[];
}

export interface PlayerAction {
  player_id: string;
  player_name: string;
  action: 'fold' | 'check' | 'call' | 'raise' | 'allin';
  amount: number;
}

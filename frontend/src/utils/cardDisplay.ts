import type { Suit } from '../types';

const RANK_DISPLAY: Record<number, string> = {
  14: 'A', 13: 'K', 12: 'Q', 11: 'J', 10: '10',
  9: '9', 8: '8', 7: '7', 6: '6', 5: '5', 4: '4', 3: '3', 2: '2',
};

const SUIT_SYMBOL: Record<string, string> = {
  Hearts: '\u2665',   // ♥
  Diamonds: '\u2666', // ♦
  Clubs: '\u2663',    // ♣
  Spades: '\u2660',   // ♠
};

const CHAR_TO_RANK: Record<string, number> = {
  'A': 14, 'K': 13, 'Q': 12, 'J': 11, 'T': 10,
  '9': 9, '8': 8, '7': 7, '6': 6, '5': 5, '4': 4, '3': 3, '2': 2,
};

const SYMBOL_TO_SUIT: Record<string, Suit> = {
  '\u2665': 'Hearts',   // ♥
  '\u2666': 'Diamonds', // ♦
  '\u2663': 'Clubs',    // ♣
  '\u2660': 'Spades',   // ♠
};

export function rankToDisplay(rank: number): string {
  return RANK_DISPLAY[rank] ?? String(rank);
}

export function suitToSymbol(suit: string): string {
  return SUIT_SYMBOL[suit] ?? '';
}

export function isRedSuit(suit: string): boolean {
  return suit === 'Hearts' || suit === 'Diamonds';
}

export function charToRank(char: string): number | undefined {
  return CHAR_TO_RANK[char];
}

export function symbolToSuit(symbol: string): Suit | undefined {
  return SYMBOL_TO_SUIT[symbol];
}

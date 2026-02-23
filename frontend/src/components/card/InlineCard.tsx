import React from 'react';
import Card from './Card';
import { charToRank, symbolToSuit } from '../../utils/cardDisplay';

interface InlineCardProps {
  text: string;
}

// Matches card notations like Q♥ A♠ 7♦ T♣
const CARD_REGEX = /([2-9TJQKA])([♥♠♦♣])/g;

/**
 * Parses a text string and replaces card notations (e.g. "A♠", "Q♥")
 * with XS Card components rendered inline.
 */
const InlineCard: React.FC<InlineCardProps> = ({ text }) => {
  const parts: React.ReactNode[] = [];
  let lastIdx = 0;
  let match: RegExpExecArray | null;

  // Reset regex state
  CARD_REGEX.lastIndex = 0;

  while ((match = CARD_REGEX.exec(text)) !== null) {
    // Text before this match
    if (match.index > lastIdx) {
      parts.push(
        <span key={`text-${lastIdx}`}>{text.slice(lastIdx, match.index)}</span>
      );
    }

    const rankChar = match[1];
    const suitSymbol = match[2];
    const rank = charToRank(rankChar);
    const suit = symbolToSuit(suitSymbol);

    if (rank !== undefined && suit !== undefined) {
      parts.push(
        <Card
          key={`card-${match.index}`}
          size="xs"
          variant="face-up"
          rank={rank}
          suit={suit}
        />
      );
    } else {
      // Fallback: render as plain text if parse failed
      parts.push(
        <span key={`fallback-${match.index}`}>{match[0]}</span>
      );
    }

    lastIdx = match.index + match[0].length;
  }

  // Remaining text after last match
  if (lastIdx < text.length) {
    parts.push(<span key={`text-end`}>{text.slice(lastIdx)}</span>);
  }

  return (
    <span style={{ lineHeight: 2.1 }}>
      {parts}
    </span>
  );
};

export default InlineCard;

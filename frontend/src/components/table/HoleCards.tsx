import React from 'react';
import type { Card as CardType } from '../../types';
import Card from '../card/Card';

interface HoleCardsProps {
  cards: (CardType | null)[];
  isHumanTurn: boolean; // Fix 7: show red glow only when it's the human's turn to act
  handCount: number;    // Changes every new hand → triggers re-animation via key
}

const HoleCards: React.FC<HoleCardsProps> = ({ cards, isHumanTurn, handCount }) => {
  return (
    <div style={{
      position: 'absolute',
      bottom: 24,
      left: '50%',
      transform: 'translateX(-50%)',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      gap: 8,
    }}>
      {/* YOUR HAND label */}
      <div style={{
        fontSize: 7,
        color: 'var(--gold-d)',
        letterSpacing: 2,
        animation: 'blink 1s steps(1) infinite',
        fontFamily: 'var(--font-label)',
        whiteSpace: 'nowrap',
      }}>
        ▼ YOUR HAND
      </div>

      {/* Two hole cards */}
      <div style={{ display: 'flex', gap: 12 }}>
        {cards.slice(0, 2).map((card, i) =>
          card ? (
            <Card
              key={`${handCount}-${i}`}
              size="md"
              variant="face-up"
              rank={card.rank}
              suit={card.suit}
              glow={isHumanTurn ? 'red' : 'none'}
              style={{ animation: `cardDeal 0.4s ease-out ${i * 110}ms both` }}
            />
          ) : (
            <Card key={`${handCount}-${i}`} size="md" variant="face-down" />
          )
        )}
      </div>
    </div>
  );
};

export default HoleCards;

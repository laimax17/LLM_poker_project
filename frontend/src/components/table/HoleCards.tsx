import React from 'react';
import type { Card as CardType } from '../../types';
import Card from '../card/Card';

interface HoleCardsProps {
  cards: (CardType | null)[];
}

const HoleCards: React.FC<HoleCardsProps> = ({ cards }) => {
  return (
    <div style={{
      position: 'absolute',
      bottom: 20,
      left: '50%',
      transform: 'translateX(-50%)',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      gap: 8,
    }}>
      {/* YOUR HAND label */}
      <div style={{
        fontSize: 5,
        color: 'var(--gold-d)',
        letterSpacing: 2,
        animation: 'blink 1s steps(1) infinite',
        fontFamily: 'var(--font-label)',
        whiteSpace: 'nowrap',
      }}>
        ▼ YOUR HAND
      </div>

      {/* Two hole cards */}
      <div style={{ display: 'flex', gap: 10 }}>
        {cards.slice(0, 2).map((card, i) =>
          card ? (
            <Card
              key={i}
              size="md"
              variant="face-up"
              rank={card.rank}
              suit={card.suit}
              glow="red"
            />
          ) : (
            <Card key={i} size="md" variant="face-down" />
          )
        )}
      </div>
    </div>
  );
};

export default HoleCards;

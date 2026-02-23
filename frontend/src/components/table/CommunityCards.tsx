import React from 'react';
import type { Card as CardType } from '../../types';
import Card from '../card/Card';

interface CommunityCardsProps {
  cards: CardType[];
}

const CommunityCards: React.FC<CommunityCardsProps> = ({ cards }) => {
  return (
    <div style={{ display: 'flex', gap: 8 }}>
      {Array.from({ length: 5 }, (_, i) => {
        const card = cards[i];
        if (card) {
          return (
            <Card
              key={i}
              size="lg"
              variant="face-up"
              rank={card.rank}
              suit={card.suit}
              glow="gold"
            />
          );
        }
        return (
          <Card
            key={i}
            size="lg"
            variant="placeholder"
          />
        );
      })}
    </div>
  );
};

export default CommunityCards;

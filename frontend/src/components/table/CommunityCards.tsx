import React from 'react';
import type { Card as CardType } from '../../types';
import Card from '../card/Card';

interface CommunityCardsProps {
  cards: CardType[];
}

const CommunityCards: React.FC<CommunityCardsProps> = ({ cards }) => {
  return (
    <div style={{ display: 'flex', gap: 10 }}>
      {Array.from({ length: 5 }, (_, i) => {
        const card = cards[i];
        if (card) {
          // Key changes from 'ph-i' → 'rank-suit' when card is revealed,
          // forcing remount and replaying the cardReveal animation.
          return (
            <Card
              key={`${card.rank}-${card.suit}`}
              size="lg"
              variant="face-up"
              rank={card.rank}
              suit={card.suit}
              glow="gold"
              style={{ animation: `cardReveal 0.32s ease-out ${i * 55}ms both` }}
            />
          );
        }
        return (
          <Card
            key={`ph-${i}`}
            size="lg"
            variant="placeholder"
          />
        );
      })}
    </div>
  );
};

export default CommunityCards;

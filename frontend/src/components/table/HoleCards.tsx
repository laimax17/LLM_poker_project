import React from 'react';
import type { Card as CardType } from '../../types';
import Card from '../card/Card';
import { useT } from '../../i18n/I18nContext';

interface HoleCardsProps {
  cards: (CardType | null)[];
  isHumanTurn: boolean;
  handCount: number;
  winningCards?: CardType[];
}

function isWinCard(card: CardType, winningCards?: CardType[]): boolean {
  return winningCards?.some((wc) => wc.rank === card.rank && wc.suit === card.suit) ?? false;
}

const HoleCards: React.FC<HoleCardsProps> = ({ cards, isHumanTurn, handCount, winningCards }) => {
  const { t } = useT();
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
      <div
        style={{
          fontSize: 12,
          fontWeight: 700,
          color: isHumanTurn ? 'var(--gold-l)' : 'var(--text-dim)',
          letterSpacing: 1,
          textTransform: 'uppercase',
        }}
      >
        {t('human.yourHand')}
      </div>
      <div style={{ display: 'flex', gap: 12 }}>
        {cards.slice(0, 2).map((card, i) => {
          if (!card) return <Card key={`${handCount}-${i}`} size="md" variant="face-down" />;
          const win = isWinCard(card, winningCards);
          return (
            <Card
              key={`${handCount}-${i}`}
              size="md"
              variant="face-up"
              rank={card.rank}
              suit={card.suit}
              glow={win ? 'win' : isHumanTurn ? 'gold' : 'none'}
              style={{
                animation: win
                  ? `cardReveal 0.4s ease-out ${i * 110}ms both, winCardPulse 1.1s 0.6s ease-in-out infinite`
                  : `cardReveal 0.4s ease-out ${i * 110}ms both`,
              }}
            />
          );
        })}
      </div>
    </div>
  );
};

export default HoleCards;

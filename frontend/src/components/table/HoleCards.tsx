import React from 'react';
import type { Card as CardType } from '../../types';
import Card from '../card/Card';
import { useT } from '../../i18n/I18nContext';

interface HoleCardsProps {
  cards: (CardType | null)[];
  isHumanTurn: boolean; // Fix 7: show red glow only when it's the human's turn to act
  handCount: number;    // Changes every new hand → triggers re-animation via key
  winningCards?: CardType[];
}

function isWinCard(card: CardType, winningCards?: CardType[]): boolean {
  return winningCards?.some(wc => wc.rank === card.rank && wc.suit === card.suit) ?? false;
}

const HoleCards: React.FC<HoleCardsProps> = ({ cards, isHumanTurn, handCount, winningCards }) => {
  const { t } = useT();
  return (
    <div style={{
      position: 'absolute',
      bottom: 14,
      left: 'calc(50% - 128px)',
      transform: 'translateX(-50%)',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      gap: 8,
    }}>
      {/* YOUR HAND label */}
      <div style={{
        fontSize: 13,
        fontWeight: 700,
        color: 'var(--gold-d)',
        letterSpacing: 1,
        animation: 'blink 1s steps(1) infinite',
        fontFamily: 'var(--font-label)',
        whiteSpace: 'nowrap',
      }}>
        ▼ {t('human.yourHand')}
      </div>

      {/* Two hole cards */}
      <div style={{ display: 'flex', gap: 12 }}>
        {cards.slice(0, 2).map((card, i) => {
          if (!card) return <Card key={`${handCount}-${i}`} size="lg" variant="face-down" />;
          const win = isWinCard(card, winningCards);
          return (
            <Card
              key={`${handCount}-${i}`}
              size="lg"
              variant="face-up"
              rank={card.rank}
              suit={card.suit}
              glow={win ? 'win' : isHumanTurn ? 'red' : 'none'}
              style={{
                animation: win
                  ? `cardDeal 0.4s ease-out ${i * 110}ms both, winCardPulse 1.1s 0.6s ease-in-out infinite`
                  : `cardDeal 0.4s ease-out ${i * 110}ms both`,
              }}
            />
          );
        })}
      </div>
    </div>
  );
};

export default HoleCards;

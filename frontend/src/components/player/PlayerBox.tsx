import React from 'react';
import type { Player, Card as CardType } from '../../types';
import Card from '../card/Card';
import BotSpeechBubble from './BotSpeechBubble';
import ChipStack from '../table/ChipStack';
import { useGameStore } from '../../store/useGameStore';
import { useT } from '../../i18n/I18nContext';

interface PlayerBoxProps {
  player: Player;
  isCurrentTurn: boolean;
  chipBubbleSide: 'right' | 'left';
  badge?: string;   // 'BTN' | 'SB' | 'BB' | 'UTG' | 'HJ' | 'CO'
}

function getStatusText(
  player: Player,
  isCurrentTurn: boolean,
  t: (key: string) => string,
): { text: string; color: string } {
  if (!player.is_active) return { text: t('status.fold'), color: 'var(--brown)' };
  if (player.is_all_in)  return { text: t('status.allin'), color: '#ffcc00' };
  if (isCurrentTurn)     return { text: t('status.thinking'), color: '#ffcc00' };
  if (player.current_bet > 0) return { text: `${t('status.bet')} $${player.current_bet}`, color: '#ffcc00' };
  return { text: t('status.waiting'), color: 'var(--gold-d)' };
}

const PlayerBox: React.FC<PlayerBoxProps> = ({
  player,
  isCurrentTurn,
  chipBubbleSide,
  badge,
}) => {
  const { t } = useT();
  const isFolded = !player.is_active;
  const status = getStatusText(player, isCurrentTurn, t);
  // Subscribe directly to this bot's current thought (avoids prop drilling)
  const thought = useGameStore(s => s.botThoughts[player.id]);

  const boxStyle: React.CSSProperties = {
    background: 'rgba(10, 9, 0, 0.88)',
    border: '2px solid var(--brown)',
    padding: '20px 28px',
    width: 400,
    clipPath: 'var(--clip-sm)',
    opacity: isFolded ? 0.3 : 1,
    flexShrink: 0,
    transition: 'border-color 0.2s ease, box-shadow 0.2s ease',
  };

  const activeBoxStyle: React.CSSProperties = isCurrentTurn && player.is_active ? {
    borderColor: 'var(--gold)',
    boxShadow: '0 0 14px rgba(200,160,64,0.45)',
    animation: 'gold-pulse 0.8s steps(1) infinite',
  } : {};

  // Show face-up cards only at showdown (cards will be Card objects instead of null)
  const showCards = player.hand.length === 2 && player.hand[0] !== null && player.hand[1] !== null;
  const hasChipBubble = player.current_bet > 0 && player.is_active;

  const bubbleEl = hasChipBubble ? (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      gap: 5,
      alignSelf: 'center',
      flexShrink: 0,
    }}>
      {/* Chip pile — key forces remount+animation when bet changes */}
      <ChipStack key={player.current_bet} amount={player.current_bet} size="lg" />
      {/* Amount label below the stack */}
      <div style={{
        fontFamily: 'var(--font-ui)',
        fontSize: 14,
        color: 'var(--gold)',
        background: '#1a0e00',
        border: '1px solid var(--gold-d)',
        padding: '4px 10px',
        whiteSpace: 'nowrap',
      }}>
        <span
          key={player.current_bet}
          style={{ display: 'inline-block', animation: 'numUpdate 0.35s ease-out' }}
        >
          ${player.current_bet}
        </span>
      </div>
    </div>
  ) : null;

  return (
    <div style={{
      display: 'flex',
      flexDirection: chipBubbleSide === 'right' ? 'row' : 'row-reverse',
      alignItems: 'center',
      gap: 10,
    }}>
      {/* Box wrapper — badge sits outside the clipped div so it won't be cut off */}
      <div style={{ position: 'relative' }}>
        {/* Position badge — OUTSIDE clipPath to avoid clipping */}
        {badge && (
          <div style={{
            position: 'absolute',
            top: -14,
            right: 5,
            background: 'var(--gold)',
            color: '#000',
            fontSize: 14,
            padding: '4px 10px',
            fontFamily: 'var(--font-ui)',
            lineHeight: 1.4,
            zIndex: 2,
          }}>
            {badge}
          </div>
        )}

        {/* Main pbox — has clipPath */}
        <div style={{ ...boxStyle, ...activeBoxStyle }}>
          {/* Bot name */}
          <div style={{
            fontFamily: 'var(--font-ui)',
            fontSize: 22,
            color: 'var(--gold)',
            marginBottom: 6,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}>
            {player.name}
          </div>

          {/* Chips — key replays numUpdate animation when chips change */}
          <div style={{
            fontSize: 16,
            color: 'var(--gold-l)',
            marginBottom: 5,
            fontFamily: 'var(--font-label)',
          }}>
            <span
              key={player.chips}
              style={{ display: 'inline-block', animation: 'numUpdate 0.35s ease-out' }}
            >
              ${player.chips.toLocaleString()}
            </span>
          </div>

          {/* Status */}
          <div style={{
            fontSize: 16,
            color: status.color,
            fontFamily: 'var(--font-label)',
          }}>
            {status.text}
          </div>

          {/* Cards (face-down or face-up at showdown) */}
          <div style={{ display: 'flex', gap: 8, marginTop: 10 }}>
            {showCards ? (
              <>
                <Card
                  size="md"
                  variant="face-up"
                  rank={(player.hand[0] as CardType).rank}
                  suit={(player.hand[0] as CardType).suit}
                />
                <Card
                  size="md"
                  variant="face-up"
                  rank={(player.hand[1] as CardType).rank}
                  suit={(player.hand[1] as CardType).suit}
                />
              </>
            ) : (
              <>
                <Card size="md" variant="face-down" />
                <Card size="md" variant="face-down" />
              </>
            )}
          </div>

          {/* Speech bubble — floats outside this box via absolute positioning */}
          {thought && (
            <BotSpeechBubble text={thought.chat} side={chipBubbleSide} fading={thought.fading} />
          )}
        </div>
      </div>

      {/* Chip bubble */}
      {bubbleEl}
    </div>
  );
};

export default PlayerBox;

import React from 'react';
import type { Player, Card as CardType } from '../../types';
import Card from '../card/Card';
import BotSpeechBubble from './BotSpeechBubble';
import { useGameStore } from '../../store/useGameStore';

interface PlayerBoxProps {
  player: Player;
  isCurrentTurn: boolean;
  chipBubbleSide: 'right' | 'left';
  badge?: string;   // 'BTN' | 'SB' | 'BB' | 'UTG' | 'HJ' | 'CO'
}

function getStatusText(player: Player, isCurrentTurn: boolean): { text: string; color: string } {
  if (!player.is_active) return { text: 'FOLD', color: 'var(--brown)' };
  if (player.is_all_in)  return { text: 'ALL IN', color: '#ffcc00' };
  if (isCurrentTurn)     return { text: 'THINKING ▌', color: '#ffcc00' };
  if (player.current_bet > 0) return { text: `BET $${player.current_bet}`, color: '#ffcc00' };
  return { text: 'WAITING', color: 'var(--gold-d)' };
}

const PlayerBox: React.FC<PlayerBoxProps> = ({
  player,
  isCurrentTurn,
  chipBubbleSide,
  badge,
}) => {
  const isFolded = !player.is_active;
  const status = getStatusText(player, isCurrentTurn);
  // Subscribe directly to this bot's current thought (avoids prop drilling)
  const thought = useGameStore(s => s.botThoughts[player.id]);

  const boxStyle: React.CSSProperties = {
    background: 'rgba(10, 9, 0, 0.88)',
    border: '2px solid var(--brown)',
    padding: '10px 12px',
    width: 180,
    position: 'relative',
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
      fontFamily: 'var(--font-ui)',
      fontSize: 7,
      background: '#1a0e00',
      border: '1px solid var(--gold-d)',
      color: 'var(--gold)',
      padding: '3px 8px',
      alignSelf: 'center',
      flexShrink: 0,
      whiteSpace: 'nowrap',
    }}>
      ${player.current_bet}
    </div>
  ) : null;

  return (
    <div style={{
      display: 'flex',
      flexDirection: chipBubbleSide === 'right' ? 'row' : 'row-reverse',
      alignItems: 'center',
      gap: 6,
    }}>
      {/* Main pbox */}
      <div style={{ ...boxStyle, ...activeBoxStyle }}>
        {/* Position badge */}
        {badge && (
          <div style={{
            position: 'absolute',
            top: -10,
            right: 5,
            background: 'var(--gold)',
            color: '#000',
            fontSize: 6,
            padding: '2px 6px',
            fontFamily: 'var(--font-ui)',
            lineHeight: 1.4,
          }}>
            {badge}
          </div>
        )}

        {/* Bot name */}
        <div style={{
          fontFamily: 'var(--font-ui)',
          fontSize: 10,
          color: 'var(--gold)',
          marginBottom: 4,
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap',
        }}>
          {player.name}
        </div>

        {/* Chips */}
        <div style={{
          fontSize: 7,
          color: 'var(--gold-l)',
          marginBottom: 3,
          fontFamily: 'var(--font-label)',
        }}>
          ${player.chips.toLocaleString()}
        </div>

        {/* Status */}
        <div style={{
          fontSize: 7,
          color: status.color,
          fontFamily: 'var(--font-label)',
        }}>
          {status.text}
        </div>

        {/* Cards (face-down or face-up at showdown) */}
        <div style={{ display: 'flex', gap: 4, marginTop: 6 }}>
          {showCards ? (
            <>
              <Card
                size="sm"
                variant="face-up"
                rank={(player.hand[0] as CardType).rank}
                suit={(player.hand[0] as CardType).suit}
              />
              <Card
                size="sm"
                variant="face-up"
                rank={(player.hand[1] as CardType).rank}
                suit={(player.hand[1] as CardType).suit}
              />
            </>
          ) : (
            <>
              <Card size="sm" variant="face-down" />
              <Card size="sm" variant="face-down" />
            </>
          )}
        </div>

        {/* Speech bubble — floats outside this box via absolute positioning */}
        {thought && (
          <BotSpeechBubble text={thought.chat} side={chipBubbleSide} fading={thought.fading} />
        )}
      </div>

      {/* Chip bubble */}
      {bubbleEl}
    </div>
  );
};

export default PlayerBox;

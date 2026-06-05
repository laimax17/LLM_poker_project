import React from 'react';
import type { Player, Card as CardType } from '../../types';
import Card from '../card/Card';
import { useGameStore } from '../../store/useGameStore';
import { useT } from '../../i18n/I18nContext';

interface PlayerBoxProps {
  player: Player;
  isCurrentTurn: boolean;
  badge?: string; // 'BTN' | 'SB' | 'BB' | ...
  winningCards?: CardType[];
  compact?: boolean;
}

const AVATAR_COLORS = ['#d6504a', '#4aa3d6', '#9b6bd6', '#2fa566', '#e8743a', '#d6a84a'];

function isWinCard(card: CardType, winningCards?: CardType[]): boolean {
  return winningCards?.some((wc) => wc.rank === card.rank && wc.suit === card.suit) ?? false;
}

function getStatus(
  player: Player,
  isCurrentTurn: boolean,
  t: (k: string) => string,
): { text: string; color: string } {
  if (!player.is_active) return { text: t('status.fold'), color: 'var(--text-dim)' };
  if (player.is_all_in) return { text: t('status.allin'), color: 'var(--allin)' };
  if (isCurrentTurn) return { text: t('status.thinking'), color: 'var(--gold-l)' };
  return { text: '', color: 'var(--text-dim)' };
}

// Stable colour per bot id
function avatarColor(id: string): string {
  let h = 0;
  for (let i = 0; i < id.length; i++) h = (h * 31 + id.charCodeAt(i)) >>> 0;
  return AVATAR_COLORS[h % AVATAR_COLORS.length];
}

const PlayerBox: React.FC<PlayerBoxProps> = ({ player, isCurrentTurn, badge, winningCards, compact = false }) => {
  const { t } = useT();
  const thought = useGameStore((s) => s.botThoughts[player.id]);
  const isThinking = useGameStore((s) => s.thinkingBots[player.id] ?? false);

  const isFolded = !player.is_active;
  const status = getStatus(player, isCurrentTurn, t);
  const showCards = player.hand.length === 2 && player.hand[0] !== null && player.hand[1] !== null;
  const accent = avatarColor(player.id);
  const cardSize = compact ? 'xs' : 'sm';
  const boxW = compact ? 116 : 138;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: boxW, flexShrink: 0 }}>
      {/* Speech bubble / thinking dots */}
      <div style={{ height: 30, display: 'flex', alignItems: 'flex-end', marginBottom: 3 }}>
        {thought ? (
          <div
            style={{
              background: 'var(--surface2)',
              border: '1px solid var(--line)',
              borderRadius: 12,
              padding: '5px 10px',
              fontSize: 12,
              color: 'var(--text)',
              maxWidth: 160,
              textAlign: 'center',
              lineHeight: 1.25,
              boxShadow: '0 2px 8px rgba(0,0,0,0.4)',
              animation: 'popIn 0.2s ease-out',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              opacity: thought.fading ? 0 : 1,
              transition: 'opacity 0.4s',
            }}
          >
            {thought.chat}
          </div>
        ) : isThinking ? (
          <span style={{ color: 'var(--gold)', fontSize: 18, animation: 'blink 1s steps(1) infinite' }}>● ● ●</span>
        ) : null}
      </div>

      {/* Mini hole cards peeking above the pod */}
      <div style={{ display: 'flex', gap: 3, marginBottom: -12, zIndex: 1 }}>
        {showCards ? (
          [player.hand[0] as CardType, player.hand[1] as CardType].map((c, i) => (
            <Card
              key={i}
              size={cardSize}
              variant="face-up"
              rank={c.rank}
              suit={c.suit}
              glow={isWinCard(c, winningCards) ? 'win' : 'none'}
              style={isWinCard(c, winningCards) ? { animation: 'winCardPulse 1.1s ease-in-out infinite' } : undefined}
            />
          ))
        ) : (
          <>
            <Card size={cardSize} variant="face-down" />
            <Card size={cardSize} variant="face-down" />
          </>
        )}
      </div>

      {/* Pod */}
      <div
        style={{
          position: 'relative',
          width: '100%',
          background: 'var(--surface)',
          border: `2px solid ${isCurrentTurn && !isFolded ? 'var(--gold)' : 'var(--line)'}`,
          borderRadius: 14,
          padding: '16px 8px 9px',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 2,
          opacity: isFolded ? 0.45 : 1,
          transition: 'opacity 0.3s, border-color 0.2s',
          animation: isCurrentTurn && !isFolded ? 'turn-pulse 1.4s ease-in-out infinite' : 'none',
        }}
      >
        {/* Badge */}
        {badge && (
          <div
            style={{
              position: 'absolute',
              top: -10,
              left: 8,
              background: 'var(--gold)',
              color: '#1a1208',
              fontSize: 10,
              fontWeight: 800,
              padding: '2px 7px',
              borderRadius: 8,
            }}
          >
            {badge}
          </div>
        )}

        {/* Avatar */}
        <div
          style={{
            width: 34,
            height: 34,
            borderRadius: '50%',
            background: accent,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontWeight: 800,
            fontSize: 16,
            color: '#fff',
            marginTop: -28,
            border: '3px solid var(--surface)',
            boxShadow: '0 2px 6px rgba(0,0,0,0.4)',
          }}
        >
          {(player.name || '?').charAt(0).toUpperCase()}
        </div>

        {/* Name */}
        <div
          style={{
            fontWeight: 700,
            fontSize: 13,
            color: 'var(--text)',
            maxWidth: '100%',
            whiteSpace: 'nowrap',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
          }}
        >
          {player.name}
        </div>

        {/* Chips */}
        <div
          key={player.chips}
          style={{
            fontFamily: 'var(--font-ui)',
            fontSize: 16,
            fontWeight: 700,
            color: player.is_all_in ? 'var(--allin)' : 'var(--gold-l)',
            animation: 'numUpdate 0.35s ease-out',
          }}
        >
          {player.is_all_in ? t('status.allin') : player.chips.toLocaleString()}
        </div>

        {/* Status line */}
        {status.text && (
          <div style={{ fontSize: 11, fontWeight: 600, color: status.color, display: 'flex', alignItems: 'center', gap: 4 }}>
            {isThinking && (
              <span
                style={{
                  width: 8,
                  height: 8,
                  borderRadius: '50%',
                  border: '2px solid var(--gold)',
                  borderTopColor: 'transparent',
                  animation: 'spin 0.7s linear infinite',
                }}
              />
            )}
            {status.text}
          </div>
        )}
      </div>

      {/* Bet chip */}
      {player.current_bet > 0 && player.is_active && (
        <div
          key={player.current_bet}
          style={{
            marginTop: 6,
            display: 'flex',
            alignItems: 'center',
            gap: 5,
            background: 'rgba(0,0,0,0.4)',
            border: '1px solid var(--gold-d)',
            borderRadius: 16,
            padding: '3px 9px',
            fontSize: 12,
            fontWeight: 700,
            color: 'var(--gold-l)',
            animation: 'numUpdate 0.35s ease-out',
          }}
        >
          <span style={{ width: 9, height: 9, borderRadius: '50%', background: 'var(--gold)' }} />
          {player.current_bet.toLocaleString()}
        </div>
      )}
    </div>
  );
};

export default PlayerBox;

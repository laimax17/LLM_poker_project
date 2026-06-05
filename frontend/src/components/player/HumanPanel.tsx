import React from 'react';
import type { Player } from '../../types';
import { useT } from '../../i18n/I18nContext';

interface HumanPanelProps {
  player: Player;
  dealerIdx: number;
  playerIdx: number;
  totalPlayers: number;
  isHumanTurn?: boolean;
}

function derivePositionLabel(playerIdx: number, dealerIdx: number, totalPlayers: number): string {
  const sbIdx = (dealerIdx + 1) % totalPlayers;
  const bbIdx = (dealerIdx + 2) % totalPlayers;
  if (playerIdx === dealerIdx) return 'BTN';
  if (playerIdx === sbIdx) return 'SB';
  if (playerIdx === bbIdx) return 'BB';
  const pos = (playerIdx - dealerIdx + totalPlayers) % totalPlayers;
  if (pos === 3) return 'UTG';
  if (pos === 4) return 'HJ';
  if (pos === 5) return 'CO';
  return '';
}

function isInPosition(playerIdx: number, dealerIdx: number, totalPlayers: number): boolean {
  const pos = (playerIdx - dealerIdx + totalPlayers) % totalPlayers;
  return pos === 0 || pos >= totalPlayers - 2;
}

const HumanPanel: React.FC<HumanPanelProps> = ({ player, dealerIdx, playerIdx, totalPlayers, isHumanTurn }) => {
  const { t } = useT();
  const posLabel = derivePositionLabel(playerIdx, dealerIdx, totalPlayers);
  const ip = isInPosition(playerIdx, dealerIdx, totalPlayers);
  if (!player) return null;

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 14,
        background: 'var(--surface)',
        border: `2px solid ${isHumanTurn ? 'var(--gold)' : 'var(--line)'}`,
        borderRadius: 16,
        padding: '8px 18px',
        opacity: player.is_active ? 1 : 0.45,
        animation: isHumanTurn ? 'turn-pulse 1.4s ease-in-out infinite' : 'none',
      }}
    >
      {/* Avatar */}
      <div
        style={{
          width: 38,
          height: 38,
          borderRadius: '50%',
          background: 'linear-gradient(180deg, var(--gold-l), var(--gold-d))',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontWeight: 800,
          fontSize: 18,
          color: '#2a1d00',
          flexShrink: 0,
        }}
      >
        {(player.name || 'Y').charAt(0).toUpperCase()}
      </div>

      {/* Name + position */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
        <span style={{ fontWeight: 700, fontSize: 14, color: 'var(--text)' }}>
          {player.name}
          {isHumanTurn && <span style={{ color: 'var(--gold)', marginLeft: 8, fontSize: 12 }}>● {t('human.yourTurn')}</span>}
        </span>
        <span style={{ fontSize: 12, fontWeight: 600, color: ip ? '#2fa566' : 'var(--text-dim)', display: 'flex', alignItems: 'center', gap: 5 }}>
          <span style={{ color: ip ? '#2fa566' : '#cc6666' }}>●</span>
          {posLabel && <span>{posLabel}</span>}
          <span>{ip ? t('human.inPos') : t('human.oop')}</span>
        </span>
      </div>

      {/* Chips */}
      <div
        key={player.chips}
        style={{
          fontFamily: 'var(--font-ui)',
          fontSize: 24,
          fontWeight: 700,
          color: player.is_all_in ? 'var(--allin)' : 'var(--gold-l)',
          animation: 'numUpdate 0.35s ease-out',
          marginLeft: 4,
        }}
      >
        {player.is_all_in ? t('status.allin') : player.chips.toLocaleString()}
      </div>

      {/* Current bet */}
      {player.current_bet > 0 && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            background: 'rgba(0,0,0,0.4)',
            border: '1px solid var(--gold-d)',
            borderRadius: 16,
            padding: '4px 11px',
            fontSize: 13,
            fontWeight: 700,
            color: 'var(--gold-l)',
          }}
        >
          <span style={{ width: 10, height: 10, borderRadius: '50%', background: 'var(--gold)' }} />
          {t('status.bet')} {player.current_bet.toLocaleString()}
        </div>
      )}
    </div>
  );
};

export default HumanPanel;

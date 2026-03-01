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
  // UTG, HJ, CO approximations for 6-max
  const pos = (playerIdx - dealerIdx + totalPlayers) % totalPlayers;
  if (pos === 3) return 'UTG';
  if (pos === 4) return 'HJ';
  if (pos === 5) return 'CO';
  return '';
}

function isInPosition(playerIdx: number, dealerIdx: number, totalPlayers: number): boolean {
  // BTN (pos=0) acts last postflop — most in position.
  // HJ (pos=totalPlayers-2) and CO (pos=totalPlayers-1) also act late.
  // SB (pos=1), BB (pos=2), UTG (pos=3) act early — out of position.
  const pos = (playerIdx - dealerIdx + totalPlayers) % totalPlayers;
  return pos === 0 || pos >= totalPlayers - 2;
}

const HumanPanel: React.FC<HumanPanelProps> = ({
  player,
  dealerIdx,
  playerIdx,
  totalPlayers,
  isHumanTurn,
}) => {
  const { t } = useT();
  const posLabel = derivePositionLabel(playerIdx, dealerIdx, totalPlayers);
  const ip = isInPosition(playerIdx, dealerIdx, totalPlayers);

  return (
    <div style={{
      background: 'var(--surface)',
      border: '3px solid var(--gold-l)',
      boxShadow: '0 0 20px rgba(232,208,128,0.2), 3px 3px 0 #000',
      padding: '14px 18px',
      minWidth: 180,
      clipPath: 'var(--clip-md)',
      opacity: player.is_active ? 1 : 0.3,
      transition: 'opacity 0.3s ease',
    }}>
      {/* YOUR TURN indicator — blinks when it's the human's action */}
      {isHumanTurn && (
        <div style={{
          fontSize: 7,
          color: 'var(--gold)',
          fontFamily: 'var(--font-label)',
          letterSpacing: 2,
          animation: 'blink 0.6s steps(1) infinite',
          marginBottom: 5,
          textAlign: 'center',
        }}>
          ◈ {t('human.yourTurn')}
        </div>
      )}

      {/* YOU tag */}
      <div style={{
        display: 'inline-block',
        fontSize: 7,
        background: 'var(--gold)',
        color: '#000',
        padding: '2px 6px',
        marginBottom: 6,
        fontFamily: 'var(--font-label)',
      }}>
        {t('human.you')}
      </div>

      {/* Player name */}
      <div style={{
        fontFamily: 'var(--font-ui)',
        fontSize: 14,
        color: 'var(--gold-l)',
        textShadow: '0 0 8px rgba(232,208,128,0.5)',
        marginBottom: 5,
        letterSpacing: 1,
      }}>
        {player.name}
      </div>

      {/* Chips — key replays numUpdate animation when chips change */}
      <div style={{
        fontSize: 11,
        color: 'var(--gold)',
        marginBottom: 4,
        fontFamily: 'var(--font-label)',
      }}>
        <span
          key={player.chips}
          style={{ display: 'inline-block', animation: 'numUpdate 0.35s ease-out' }}
        >
          ${player.chips.toLocaleString()}
        </span>
      </div>

      {/* Position + status */}
      <div style={{
        fontSize: 8,
        color: ip ? '#66cc88' : 'var(--gold-d)',
        fontFamily: 'var(--font-label)',
        display: 'flex',
        alignItems: 'center',
        gap: 4,
      }}>
        <span style={{ color: ip ? '#66cc88' : '#cc6666' }}>●</span>
        {posLabel && <span>{posLabel}</span>}
        <span>{ip ? t('human.inPos') : t('human.oop')}</span>
      </div>

      {/* Current bet if any */}
      {player.current_bet > 0 && (
        <div style={{
          marginTop: 4,
          fontSize: 7,
          color: '#ffcc00',
          fontFamily: 'var(--font-label)',
        }}>
          {t('status.bet')}: ${player.current_bet}
        </div>
      )}
    </div>
  );
};

export default HumanPanel;

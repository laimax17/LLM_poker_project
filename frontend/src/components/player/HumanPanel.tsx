import React from 'react';
import type { Player } from '../../types';

interface HumanPanelProps {
  player: Player;
  dealerIdx: number;
  playerIdx: number;
  totalPlayers: number;
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
}) => {
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
        YOU
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

      {/* Chips */}
      <div style={{
        fontSize: 11,
        color: 'var(--gold)',
        marginBottom: 4,
        fontFamily: 'var(--font-label)',
      }}>
        ${player.chips.toLocaleString()}
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
        <span>{ip ? 'IN POS' : 'OOP'}</span>
      </div>

      {/* Current bet if any */}
      {player.current_bet > 0 && (
        <div style={{
          marginTop: 4,
          fontSize: 7,
          color: '#ffcc00',
          fontFamily: 'var(--font-label)',
        }}>
          BET: ${player.current_bet}
        </div>
      )}
    </div>
  );
};

export default HumanPanel;

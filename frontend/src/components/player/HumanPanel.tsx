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
  // In position = closer to the button relative to opponents
  const pos = (playerIdx - dealerIdx + totalPlayers) % totalPlayers;
  return pos >= Math.floor(totalPlayers / 2);
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
      padding: '12px 16px',
      minWidth: 150,
      clipPath: 'var(--clip-md)',
    }}>
      {/* YOU tag */}
      <div style={{
        display: 'inline-block',
        fontSize: 5,
        background: 'var(--gold)',
        color: '#000',
        padding: '2px 5px',
        marginBottom: 6,
        fontFamily: 'var(--font-label)',
      }}>
        YOU
      </div>

      {/* Player name */}
      <div style={{
        fontFamily: 'var(--font-ui)',
        fontSize: 11,
        color: 'var(--gold-l)',
        textShadow: '0 0 8px rgba(232,208,128,0.5)',
        marginBottom: 5,
        letterSpacing: 1,
      }}>
        {player.name}
      </div>

      {/* Chips */}
      <div style={{
        fontSize: 8,
        color: 'var(--gold)',
        marginBottom: 4,
        fontFamily: 'var(--font-label)',
      }}>
        ${player.chips.toLocaleString()}
      </div>

      {/* Position + status */}
      <div style={{
        fontSize: 6,
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
          fontSize: 5,
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

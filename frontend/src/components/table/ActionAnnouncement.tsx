import React from 'react';
import type { PlayerAction } from '../../types';

interface ActionAnnouncementProps {
  action: PlayerAction;
}

function formatAction(action: PlayerAction): string {
  switch (action.action) {
    case 'fold':  return 'FOLD';
    case 'check': return 'CHECK';
    case 'call':  return 'CALL';
    case 'raise': return `RAISE $${action.amount}`;
    case 'allin': return 'ALL IN';
    default:      return action.action.toUpperCase();
  }
}

function getActionColor(action: string): string {
  switch (action) {
    case 'fold':  return '#ff8888';
    case 'check': return '#88ddaa';
    case 'call':  return '#88ddaa';
    case 'raise': return '#e8d080';
    case 'allin': return '#ffcc00';
    default:      return '#e8d080';
  }
}

const ActionAnnouncement: React.FC<ActionAnnouncementProps> = ({ action }) => {
  const color = getActionColor(action.action);
  const text = formatAction(action);

  return (
    <div style={{
      position: 'absolute',
      top: '38%',
      left: '50%',
      zIndex: 12,
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      pointerEvents: 'none',
      animation: 'actionAnnounce 1.5s ease-out forwards',
    }}>
      {/* Player name */}
      <div style={{
        fontFamily: 'var(--font-label)',
        fontSize: 9,
        color: 'var(--gold-d)',
        letterSpacing: 2,
        marginBottom: 2,
      }}>
        {action.player_name}
      </div>
      {/* Action text */}
      <div style={{
        fontFamily: 'var(--font-ui)',
        fontSize: 24,
        color,
        letterSpacing: 3,
        textShadow: `0 0 12px ${color}, 0 0 24px ${color}40`,
        whiteSpace: 'nowrap',
      }}>
        {text}
      </div>
    </div>
  );
};

export default ActionAnnouncement;

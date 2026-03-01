import React from 'react';
import type { PlayerAction } from '../../types';
import { useT } from '../../i18n/I18nContext';

interface ActionAnnouncementProps {
  action: PlayerAction;
}

function formatAction(action: PlayerAction, t: (key: string) => string): string {
  switch (action.action) {
    case 'fold':  return t('action.fold');
    case 'check': return t('action.check');
    case 'call':  return t('action.call');
    case 'raise': return `${t('action.raise')} $${action.amount}`;
    case 'allin': return t('action.allin');
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
  const { t } = useT();
  const color = getActionColor(action.action);
  const text = formatAction(action, t);

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

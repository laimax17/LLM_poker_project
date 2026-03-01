import React from 'react';
import { useT } from '../../i18n/I18nContext';

interface DealerBadgeProps {
  isDealing: boolean;
  isRevealing: boolean;
  isShowdown: boolean;
}

const DealerBadge: React.FC<DealerBadgeProps> = ({ isDealing, isRevealing, isShowdown }) => {
  const { t } = useT();
  const active = isDealing || isRevealing;
  const label = isShowdown
    ? t('dealer.showdown')
    : active
      ? t('dealer.dealing')
      : t('dealer.label');

  return (
    <div style={{
      position: 'absolute',
      top: 8,
      left: '50%',
      transform: 'translateX(-50%)',
      background: 'rgba(10, 9, 0, 0.92)',
      border: `2px solid ${isShowdown ? 'var(--gold-l)' : 'var(--gold)'}`,
      padding: '6px 16px',
      clipPath: 'var(--clip-sm)',
      zIndex: 8,
      fontFamily: 'var(--font-ui)',
      fontSize: 10,
      color: isShowdown ? 'var(--gold-l)' : 'var(--gold)',
      letterSpacing: 2,
      whiteSpace: 'nowrap',
      textShadow: isShowdown ? '0 0 8px rgba(200,160,64,0.6)' : 'none',
      animation: active ? 'dealerPulse 0.8s ease-in-out infinite' : 'none',
      boxShadow: '3px 3px 0 #000',
      pointerEvents: 'none',
    }}>
      {label}
    </div>
  );
};

export default DealerBadge;

import React from 'react';
import type { StandingEntry } from '../../types';
import { useT } from '../../i18n/I18nContext';

interface StandingsModalProps {
  standings: StandingEntry[];
  onPlayAgain: () => void;
}

const MEDAL: Record<number, string> = { 1: '🥇', 2: '🥈', 3: '🥉' };

const StandingsModal: React.FC<StandingsModalProps> = ({ standings, onPlayAgain }) => {
  const { t } = useT();
  const human = standings.find((s) => s.id === 'human');
  const won = human?.place === 1;

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(0,0,0,0.82)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 2000,
        padding: 16,
      }}
    >
      <div
        style={{
          background: 'var(--surface)',
          border: '4px solid var(--gold)',
          boxShadow: '0 0 28px rgba(200,160,64,0.2)',
          padding: '22px 24px',
          maxWidth: 440,
          width: '100%',
          maxHeight: '86vh',
          overflowY: 'auto',
          clipPath: 'var(--clip-md)',
        }}
      >
        <div
          style={{
            fontFamily: 'var(--font-ui)',
            fontSize: 22,
            color: won ? '#ffcc00' : 'var(--gold)',
            textShadow: won ? '0 0 16px rgba(255,204,0,0.6)' : undefined,
            textAlign: 'center',
            letterSpacing: 2,
            marginBottom: 6,
          }}
        >
          {won ? t('tour.youWin') : t('tour.over')}
        </div>
        {human && (
          <div
            style={{
              textAlign: 'center',
              fontFamily: 'var(--font-label)',
              fontSize: 9,
              color: 'var(--gold-d)',
              marginBottom: 18,
            }}
          >
            {t('tour.yourFinish')} #{human.place} / {standings.length}
          </div>
        )}

        {standings.map((s) => {
          const isHuman = s.id === 'human';
          return (
            <div
              key={s.id}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '8px 12px',
                marginBottom: 6,
                border: `2px solid ${isHuman ? 'var(--gold)' : 'var(--brown)'}`,
                background: isHuman ? 'rgba(200,160,64,0.08)' : 'transparent',
              }}
            >
              <span style={{ fontFamily: 'var(--font-ui)', fontSize: 13, color: 'var(--gold)' }}>
                {MEDAL[s.place] ?? `#${s.place}`}
              </span>
              <span
                style={{
                  flex: 1,
                  marginLeft: 12,
                  fontFamily: 'var(--font-label)',
                  fontSize: 9,
                  color: isHuman ? 'var(--gold-l)' : 'var(--gold)',
                }}
              >
                {isHuman ? t('human.you') : s.name}
              </span>
              <span
                style={{
                  fontFamily: 'var(--font-ai)',
                  fontSize: 16,
                  color: s.chips > 0 ? '#88ddaa' : 'var(--gold-d)',
                }}
              >
                {s.chips > 0 ? `$${s.chips}` : t('status.fold')}
              </span>
            </div>
          );
        })}

        <button
          className="abtn abtn-raise"
          style={{ fontSize: 12, padding: '14px 24px', marginTop: 16, width: '100%' }}
          onClick={onPlayAgain}
        >
          {t('tour.playAgain')}
        </button>
      </div>
    </div>
  );
};

export default StandingsModal;

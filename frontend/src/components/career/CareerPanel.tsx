import React from 'react';
import { getResults, computeStats, getAchievements } from '../../utils/career';
import { useT } from '../../i18n/I18nContext';

interface CareerPanelProps {
  onClose: () => void;
}

const Stat: React.FC<{ label: string; value: string }> = ({ label, value }) => (
  <div style={{ border: '2px solid var(--brown)', padding: '8px 10px', flex: 1, minWidth: 80, textAlign: 'center' }}>
    <div style={{ fontSize: 7, color: 'var(--gold-d)', marginBottom: 5, fontFamily: 'var(--font-label)' }}>{label}</div>
    <div style={{ fontFamily: 'var(--font-ui)', fontSize: 14, color: 'var(--gold)' }}>{value}</div>
  </div>
);

const CareerPanel: React.FC<CareerPanelProps> = ({ onClose }) => {
  const { t } = useT();
  const results = getResults();
  const stats = computeStats(results);
  const achievements = getAchievements(results);

  return (
    <div
      style={{
        position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.82)',
        display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 2000, padding: 16,
      }}
      onClick={onClose}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          background: 'var(--surface)', border: '4px solid var(--gold)',
          boxShadow: '0 0 28px rgba(200,160,64,0.18)', padding: '22px 24px',
          maxWidth: 480, width: '100%', maxHeight: '86vh', overflowY: 'auto', clipPath: 'var(--clip-md)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <div style={{ fontSize: 11, color: 'var(--gold)', letterSpacing: 2, fontFamily: 'var(--font-label)' }}>
            {t('career.title')}
          </div>
          <button
            onClick={onClose}
            style={{ background: 'none', border: '1px solid var(--gold-d)', color: 'var(--gold-d)', fontSize: 8, padding: '3px 8px', cursor: 'pointer', fontFamily: 'var(--font-label)' }}
          >
            ✕
          </button>
        </div>

        {stats.played === 0 ? (
          <div style={{ fontFamily: 'var(--font-ai)', fontSize: 20, color: 'var(--gold-d)', textAlign: 'center', padding: '30px 0' }}>
            {t('career.empty')}
          </div>
        ) : (
          <>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 8 }}>
              <Stat label={t('career.played')} value={String(stats.played)} />
              <Stat label={t('career.wins')} value={String(stats.wins)} />
              <Stat label={t('career.winRate')} value={`${Math.round(stats.winRate * 100)}%`} />
            </div>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 18 }}>
              <Stat label={t('career.best')} value={stats.bestPlace ? `#${stats.bestPlace}` : '—'} />
              <Stat label={t('career.avg')} value={stats.avgPlace ? stats.avgPlace.toFixed(1) : '—'} />
              <Stat label={t('career.podiums')} value={String(stats.podiums)} />
            </div>
          </>
        )}

        {/* Achievements */}
        <div style={{ fontSize: 8, color: 'var(--gold-d)', fontFamily: 'var(--font-label)', marginBottom: 10, letterSpacing: 1 }}>
          {t('career.achievements')}
        </div>
        {achievements.map((a) => (
          <div
            key={a.id}
            style={{
              display: 'flex', alignItems: 'center', gap: 10, padding: '8px 10px', marginBottom: 6,
              border: '2px solid var(--brown)',
              opacity: a.unlocked ? 1 : 0.4,
              background: a.unlocked ? 'rgba(200,160,64,0.07)' : 'transparent',
            }}
          >
            <span style={{ fontFamily: 'var(--font-ui)', fontSize: 13, color: a.unlocked ? 'var(--gold)' : 'var(--gold-d)' }}>
              {a.unlocked ? a.label : '🔒 ' + a.label.replace(/^\S+\s/, '')}
            </span>
            <span style={{ flex: 1, fontFamily: 'var(--font-ai)', fontSize: 16, color: '#c8b080', textAlign: 'right' }}>
              {a.desc}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default CareerPanel;

import React from 'react';
import type { SessionStats } from '../../types';
import { useT } from '../../i18n/I18nContext';

interface SessionStatsPanelProps {
  stats: SessionStats;
  onClose: () => void;
}

const SEVERITY_COLORS: Record<string, string> = {
  good: '#66cc88',
  bad: '#cc6666',
  neutral: 'var(--gold)',
};

const StatCell: React.FC<{ label: string; value: string; color?: string }> = ({
  label,
  value,
  color,
}) => (
  <div
    style={{
      border: '2px solid var(--brown)',
      padding: '8px 10px',
      flex: 1,
      minWidth: 80,
      textAlign: 'center',
    }}
  >
    <div
      style={{
        fontSize: 7,
        color: 'var(--gold-d)',
        marginBottom: 5,
        fontFamily: 'var(--font-label)',
      }}
    >
      {label}
    </div>
    <div
      style={{
        fontFamily: 'var(--font-ui)',
        fontSize: 13,
        color: color ?? 'var(--gold)',
      }}
    >
      {value}
    </div>
  </div>
);

const SessionStatsPanel: React.FC<SessionStatsPanelProps> = ({ stats, onClose }) => {
  const { t } = useT();
  const netColor = stats.netChips > 0 ? '#66cc88' : stats.netChips < 0 ? '#cc6666' : undefined;

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        right: 0,
        bottom: 0,
        width: 'min(380px, 92vw)',
        background: 'var(--surface)',
        borderLeft: '4px solid var(--gold)',
        boxShadow: '-4px 0 24px rgba(0,0,0,0.5)',
        zIndex: 1850,
        padding: '20px 18px',
        overflowY: 'auto',
      }}
    >
      {/* Header */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 16,
        }}
      >
        <div
          style={{
            fontSize: 11,
            color: 'var(--gold)',
            letterSpacing: 2,
            fontFamily: 'var(--font-label)',
          }}
        >
          {t('learn.statsTitle')}
        </div>
        <button
          onClick={onClose}
          style={{
            background: 'none',
            border: '1px solid var(--gold-d)',
            color: 'var(--gold-d)',
            fontSize: 8,
            padding: '3px 8px',
            cursor: 'pointer',
            fontFamily: 'var(--font-label)',
          }}
        >
          ✕
        </button>
      </div>

      {stats.handsPlayed === 0 ? (
        <div
          style={{
            fontFamily: 'var(--font-ai)',
            fontSize: 20,
            color: 'var(--gold-d)',
            textAlign: 'center',
            padding: '30px 0',
          }}
        >
          {t('learn.statsEmpty')}
        </div>
      ) : (
        <>
          {/* Core stats */}
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 10 }}>
            <StatCell label={t('learn.handsPlayed')} value={String(stats.handsPlayed)} />
            <StatCell
              label={t('learn.net')}
              value={`${stats.netChips >= 0 ? '+' : ''}${stats.netChips}`}
              color={netColor}
            />
          </div>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 10 }}>
            <StatCell label="VPIP" value={`${Math.round(stats.vpip * 100)}%`} />
            <StatCell label="PFR" value={`${Math.round(stats.pfr * 100)}%`} />
            <StatCell label="AF" value={stats.aggressionFactor.toFixed(1)} />
          </div>

          {/* Decision quality */}
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 16 }}>
            <StatCell label={t('learn.grade.correct')} value={String(stats.correct)} color="#66cc88" />
            <StatCell label={t('learn.grade.marginal')} value={String(stats.marginal)} color="#ffcc00" />
            <StatCell label={t('learn.grade.mistake')} value={String(stats.mistake)} color="#cc6666" />
          </div>

          {/* Leaks */}
          <div
            style={{
              fontSize: 8,
              color: 'var(--gold-d)',
              fontFamily: 'var(--font-label)',
              marginBottom: 8,
              letterSpacing: 1,
            }}
          >
            {t('learn.leaksTitle')}
          </div>
          {stats.leaks.length === 0 ? (
            <div
              style={{
                fontFamily: 'var(--font-ai)',
                fontSize: 18,
                color: 'var(--gold-d)',
              }}
            >
              {t('learn.leaksEmpty')}
            </div>
          ) : (
            stats.leaks.map((leak, i) => (
              <div
                key={i}
                style={{
                  border: '2px solid var(--brown)',
                  borderLeft: `4px solid ${SEVERITY_COLORS[leak.severity] ?? 'var(--gold)'}`,
                  padding: '8px 10px',
                  marginBottom: 8,
                  fontFamily: 'var(--font-ai)',
                  fontSize: 18,
                  color: '#c8b080',
                  lineHeight: 1.5,
                }}
              >
                {leak.text}
              </div>
            ))
          )}
        </>
      )}
    </div>
  );
};

export default SessionStatsPanel;

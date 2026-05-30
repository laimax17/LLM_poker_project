import React from 'react';
import type { LiveHint } from '../../types';
import { useT } from '../../i18n/I18nContext';

interface LiveHintBarProps {
  hint: LiveHint;
}

const REC_COLORS: Record<string, string> = {
  RAISE: '#ffcc00',
  FOLD: '#ff8888',
  CALL: '#88ddaa',
  CHECK: '#88ddaa',
};

const STAT_COLORS: Record<string, string> = {
  good: '#66cc88',
  bad: '#cc6666',
  hot: '#ffcc00',
  neutral: 'var(--gold)',
};

/**
 * Compact always-on math feedback strip shown above the ActionBar while it is
 * the human's turn (Learning Mode). Reuses the GTOCoach stats payload.
 */
const LiveHintBar: React.FC<LiveHintBarProps> = ({ hint }) => {
  const { t } = useT();
  const recColor = REC_COLORS[hint.recommendation] ?? 'var(--gold)';

  return (
    <div style={{ width: '100%', padding: '0 8px 6px' }}>
      <div
        style={{
          background: 'var(--surface)',
          border: '2px solid var(--gold-d)',
          boxShadow: '0 0 14px rgba(200,160,64,0.10)',
          padding: '7px 14px',
          display: 'flex',
          alignItems: 'center',
          gap: 14,
          flexWrap: 'wrap',
          clipPath: 'var(--clip-sm)',
        }}
      >
        {/* Title */}
        <span
          style={{
            fontSize: 7,
            color: 'var(--gold-d)',
            letterSpacing: 1,
            fontFamily: 'var(--font-label)',
          }}
        >
          {t('learn.hintTitle')}
        </span>

        {/* Recommendation */}
        <span
          style={{
            fontFamily: 'var(--font-ui)',
            fontSize: 13,
            color: recColor,
            textShadow:
              hint.recommendation === 'RAISE'
                ? '0 0 8px rgba(255,204,0,0.5)'
                : undefined,
          }}
        >
          {hint.recommendation}
          {hint.recommendedAmount != null && ` → $${hint.recommendedAmount}`}
        </span>

        {/* Stats (equity / pot odds / position) */}
        <div style={{ display: 'flex', gap: 14, marginLeft: 'auto', flexWrap: 'wrap' }}>
          {hint.stats
            .filter((s) => s.label !== '推荐' && s.label !== 'Recommend')
            .map((stat, i) => (
              <div
                key={i}
                style={{ display: 'flex', alignItems: 'center', gap: 6 }}
              >
                <span
                  style={{
                    fontSize: 7,
                    color: 'var(--gold-d)',
                    fontFamily: 'var(--font-label)',
                  }}
                >
                  {stat.label}
                </span>
                <span
                  style={{
                    fontFamily: 'var(--font-ui)',
                    fontSize: 12,
                    color: STAT_COLORS[stat.quality] ?? 'var(--gold)',
                  }}
                >
                  {stat.value}
                </span>
              </div>
            ))}
        </div>
      </div>
    </div>
  );
};

export default LiveHintBar;

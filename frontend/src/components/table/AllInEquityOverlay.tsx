import React from 'react';
import type { AllInEquity } from '../../types';
import { useT } from '../../i18n/I18nContext';

interface AllInEquityOverlayProps {
  data: AllInEquity;
}

const BAR_COLORS = ['#ffcc00', '#88ddaa', '#88bbff', '#ff8888', '#cc88ff', '#ffaa66'];

/** Broadcast-style all-in equity panel: each contestant's win% on a bar. */
const AllInEquityOverlay: React.FC<AllInEquityOverlayProps> = ({ data }) => {
  const { t } = useT();
  const sorted = [...data.players].sort((a, b) => b.equity - a.equity);

  return (
    <div
      style={{
        position: 'fixed',
        top: '12%',
        left: '50%',
        transform: 'translateX(-50%)',
        zIndex: 1750,
        pointerEvents: 'none',
        background: 'rgba(0,0,0,0.82)',
        border: '2px solid var(--gold)',
        boxShadow: '0 0 20px rgba(200,160,64,0.2)',
        padding: '12px 18px',
        minWidth: 260,
        clipPath: 'var(--clip-sm)',
        animation: 'fadeInSlide 0.3s ease-out',
      }}
    >
      <div
        style={{
          fontFamily: 'var(--font-label)',
          fontSize: 8,
          color: 'var(--gold-d)',
          letterSpacing: 2,
          textAlign: 'center',
          marginBottom: 10,
        }}
      >
        ◈ {t('allin.title')} ◈
      </div>

      {sorted.map((p, i) => {
        const pct = Math.round(p.equity * 100);
        const color = BAR_COLORS[i % BAR_COLORS.length];
        const isHuman = p.id === 'human';
        return (
          <div key={p.id} style={{ marginBottom: 8 }}>
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                marginBottom: 3,
              }}
            >
              <span
                style={{
                  fontFamily: 'var(--font-label)',
                  fontSize: 8,
                  color: isHuman ? 'var(--gold-l)' : 'var(--gold)',
                }}
              >
                {isHuman ? t('human.you') : p.name}
              </span>
              <span style={{ fontFamily: 'var(--font-ui)', fontSize: 12, color }}>{pct}%</span>
            </div>
            <div style={{ height: 6, background: 'var(--brown)', overflow: 'hidden' }}>
              <div
                style={{
                  height: '100%',
                  width: `${pct}%`,
                  background: color,
                  boxShadow: `0 0 6px ${color}`,
                  transition: 'width 0.5s ease-out',
                }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default AllInEquityOverlay;

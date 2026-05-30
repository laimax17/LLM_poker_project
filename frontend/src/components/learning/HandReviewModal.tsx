import React from 'react';
import type { HandReview, DecisionGrade } from '../../types';
import InlineCard from '../card/InlineCard';
import { useT } from '../../i18n/I18nContext';

interface HandReviewModalProps {
  review: HandReview;
  onClose: () => void;
}

const GRADE_META: Record<DecisionGrade, { color: string; icon: string }> = {
  correct: { color: '#66cc88', icon: '✓' },
  marginal: { color: '#ffcc00', icon: '~' },
  mistake: { color: '#cc6666', icon: '✗' },
};

const STREET_CN: Record<string, string> = {
  PREFLOP: '翻牌前',
  FLOP: '翻牌',
  TURN: '转牌',
  RIVER: '河牌',
};

const HandReviewModal: React.FC<HandReviewModalProps> = ({ review, onClose }) => {
  const { t, locale } = useT();
  const net = review.netChips;
  const netColor = net > 0 ? '#66cc88' : net < 0 ? '#cc6666' : 'var(--gold)';

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(0,0,0,0.78)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1900,
        padding: 16,
      }}
      onClick={onClose}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          position: 'relative',
          background: 'var(--surface)',
          border: '4px solid var(--gold)',
          boxShadow: '0 0 24px rgba(200,160,64,0.15)',
          padding: '20px 22px',
          maxWidth: 680,
          width: '100%',
          maxHeight: '86vh',
          overflowY: 'auto',
          clipPath: 'var(--clip-md)',
        }}
      >
        {/* Header */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: 14,
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
            {t('learn.reviewTitle')} #{review.handNumber}
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

        {/* Net result */}
        <div
          style={{
            fontFamily: 'var(--font-ui)',
            fontSize: 13,
            color: netColor,
            marginBottom: 16,
          }}
        >
          {t('learn.netResult')} {net >= 0 ? '+' : ''}
          {net}
        </div>

        {/* Decisions */}
        {review.decisions.map((d, i) => {
          const meta = GRADE_META[d.grade];
          const streetLabel = locale === 'zh' ? STREET_CN[d.street] ?? d.street : d.street;
          return (
            <div
              key={i}
              style={{
                border: '2px solid var(--brown)',
                borderLeft: `4px solid ${meta.color}`,
                padding: '10px 12px',
                marginBottom: 10,
              }}
            >
              {/* Row: street + grade */}
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: 6,
                }}
              >
                <span
                  style={{
                    fontSize: 8,
                    color: 'var(--gold-d)',
                    fontFamily: 'var(--font-label)',
                  }}
                >
                  {streetLabel} · {d.position}
                </span>
                <span
                  style={{
                    fontFamily: 'var(--font-ui)',
                    fontSize: 12,
                    color: meta.color,
                  }}
                >
                  {meta.icon} {t(`learn.grade.${d.grade}`)}
                </span>
              </div>

              {/* Cards */}
              <div
                style={{
                  fontFamily: 'var(--font-ai)',
                  fontSize: 20,
                  color: '#c8b080',
                  marginBottom: 4,
                }}
              >
                <InlineCard text={`${d.handStr}${d.boardStr ? '  |  ' + d.boardStr : ''}`} />
              </div>

              {/* GTO vs actual */}
              <div
                style={{
                  fontFamily: 'var(--font-ai)',
                  fontSize: 18,
                  color: '#c8b080',
                  lineHeight: 1.5,
                }}
              >
                <InlineCard text={d.explanation} />
              </div>
            </div>
          );
        })}

        {/* Caveat */}
        <div
          style={{
            fontSize: 8,
            color: 'var(--gold-d)',
            fontFamily: 'var(--font-label)',
            marginTop: 10,
            lineHeight: 1.6,
          }}
        >
          {t('learn.caveat')}
        </div>
      </div>
    </div>
  );
};

export default HandReviewModal;

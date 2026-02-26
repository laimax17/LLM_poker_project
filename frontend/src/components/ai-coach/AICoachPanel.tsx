import React from 'react';
import type { AICoachAdvice } from '../../types';
import InlineCard from '../card/InlineCard';

interface AICoachPanelProps {
  advice: AICoachAdvice | null;
  isLoading: boolean;
  onClose: () => void;
}

const REC_COLORS: Record<string, string> = {
  RAISE: '#ffcc00',
  FOLD:  '#ff8888',
  CALL:  '#88ddaa',
  CHECK: '#88ddaa',
};

const STAT_COLORS: Record<string, string> = {
  good:    '#66cc88',
  bad:     '#cc6666',
  hot:     '#ffcc00',
  neutral: 'var(--gold)',
};

const AICoachPanel: React.FC<AICoachPanelProps> = ({ advice, isLoading, onClose }) => {
  return (
    <div style={{
      position: 'relative',
      background: 'var(--surface)',
      border: '4px solid var(--gold)',
      boxShadow: '0 0 24px rgba(200,160,64,0.12)',
      padding: '20px 22px',
      maxWidth: 640,
      width: '100%',
      clipPath: 'var(--clip-md)',
    }}>
      {/* Top gold highlight line */}
      <div style={{
        position: 'absolute',
        top: 0, left: 0, right: 0,
        height: 3,
        background: 'linear-gradient(to right, transparent, var(--gold), transparent)',
        pointerEvents: 'none',
      }} />

      {/* Header row */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 12,
      }}>
        <div style={{
          fontSize: 10,
          color: 'var(--gold)',
          letterSpacing: 2,
          fontFamily: 'var(--font-label)',
        }}>
          ◈ AI COACH
        </div>
        <button
          onClick={onClose}
          disabled={isLoading}
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

      {/* Loading state */}
      {isLoading && (
        <div style={{
          fontFamily: 'var(--font-ai)',
          fontSize: 24,
          color: '#c8b080',
          lineHeight: 2.1,
          minHeight: 80,
          display: 'flex',
          alignItems: 'center',
        }}>
          <span style={{ animation: 'blink 1s steps(1) infinite' }}>
            ◈ AI THINKING...
          </span>
        </div>
      )}

      {/* Content */}
      {!isLoading && advice && (
        <>
          {/* Recommendation */}
          <div style={{
            fontFamily: 'var(--font-ui)',
            fontSize: 15,
            color: REC_COLORS[advice.recommendation] ?? 'var(--gold)',
            textShadow: advice.recommendation === 'RAISE'
              ? '0 0 8px rgba(255,204,0,0.5)'
              : undefined,
            marginBottom: 16,
          }}>
            推荐：{advice.recommendation}
            {advice.recommendedAmount != null && ` → $${advice.recommendedAmount}`}
          </div>

          {/* Body text with inline cards */}
          <div style={{
            fontFamily: 'var(--font-ai)',
            fontSize: 24,
            color: '#c8b080',
            lineHeight: 2.1,
            maxHeight: 320,
            overflowY: 'auto',
            marginBottom: 16,
          }}>
            {advice.body.split('\n').map((line, i) => (
              <p key={i} style={{ margin: '0 0 4px 0' }}>
                <InlineCard text={line} />
              </p>
            ))}
          </div>

          {/* Stats row */}
          {advice.stats.length > 0 && (
            <div style={{
              display: 'flex',
              gap: 10,
              flexWrap: 'wrap',
              marginTop: 16,
              paddingTop: 12,
              borderTop: '2px solid var(--brown)',
            }}>
              {advice.stats.map((stat, i) => (
                <div key={i} style={{
                  border: '2px solid var(--brown)',
                  padding: '7px 12px',
                  flex: 1,
                  minWidth: 90,
                  textAlign: 'center',
                }}>
                  <div style={{
                    fontSize: 7,
                    color: 'var(--gold-d)',
                    marginBottom: 5,
                    fontFamily: 'var(--font-label)',
                  }}>
                    {stat.label}
                  </div>
                  <div style={{
                    fontFamily: 'var(--font-ui)',
                    fontSize: 13,
                    color: STAT_COLORS[stat.quality] ?? 'var(--gold)',
                  }}>
                    {stat.value}
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {/* Empty state */}
      {!isLoading && !advice && (
        <div style={{
          fontFamily: 'var(--font-ai)',
          fontSize: 22,
          color: 'var(--gold-d)',
          textAlign: 'center',
          padding: '20px 0',
        }}>
          点击 ◈ ASK AI 获取建议
        </div>
      )}
    </div>
  );
};

export default AICoachPanel;

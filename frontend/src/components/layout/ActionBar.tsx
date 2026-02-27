import React, { useState, useEffect, useCallback } from 'react';
import type { GameState } from '../../types';

interface ActionBarProps {
  gameState: GameState;
  onAction: (action: string, amount: number) => void;
  onAskAI: () => void;
  isRequestingAdvice: boolean;
  disabled: boolean;
  showCoach: boolean;
}

const STEPS = [1, 5, 10, 20, 50, 100];

/** Clamp v to [lo, hi] */
function clamp(v: number, lo: number, hi: number): number {
  return Math.max(lo, Math.min(hi, v));
}

/** Small muted shortcut hint rendered inside a button */
const Hint: React.FC<{ k: string }> = ({ k }) => (
  <span style={{ fontSize: 6, opacity: 0.55, marginLeft: 4 }}>[{k}]</span>
);

const ActionBar: React.FC<ActionBarProps> = ({
  gameState,
  onAction,
  onAskAI,
  isRequestingAdvice,
  disabled,
  showCoach,
}) => {
  const [raiseAmount, setRaiseAmount] = useState<string>('');
  const [stepIdx, setStepIdx] = useState(2); // default step = STEPS[2] = 10

  const human = gameState.players[0];
  const toCall = Math.max(0, gameState.current_bet - (human?.current_bet ?? 0));
  const minRaise = gameState.current_bet + gameState.min_raise;
  const maxRaise = human?.chips ?? 0;

  const canCheck = toCall === 0;
  const canCall = toCall > 0;
  // Fix 5: respect raise-cap flag from backend (can_raise=false when street cap reached)
  const canRaise = maxRaise > toCall && (gameState.can_raise ?? true);

  const step = STEPS[stepIdx];
  const currentAmount = parseInt(raiseAmount, 10);

  // ─── Quick-bet helpers ─────────────────────────────────────────────────────
  const setQuickBet = useCallback((amount: number) => {
    setRaiseAmount(String(clamp(amount, minRaise, maxRaise)));
  }, [minRaise, maxRaise]);

  const adjustAmount = useCallback((delta: number) => {
    const base = isNaN(currentAmount) ? minRaise : currentAmount;
    setRaiseAmount(String(clamp(base + delta, minRaise, maxRaise)));
  }, [currentAmount, minRaise, maxRaise]);

  // ─── Raise submit ──────────────────────────────────────────────────────────
  function handleRaise() {
    const amt = parseInt(raiseAmount, 10);
    if (isNaN(amt)) return;
    const clamped = clamp(amt, minRaise, maxRaise);
    onAction('raise', clamped);
    setRaiseAmount('');
  }

  // ─── Keyboard shortcuts ────────────────────────────────────────────────────
  useEffect(() => {
    if (disabled || showCoach) return;

    const handler = (e: KeyboardEvent) => {
      // Never fire shortcuts while the user is typing in an input field
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;

      switch (e.key.toLowerCase()) {
        case 'f':
          onAction('fold', 0);
          break;
        case ' ':
        case 'c':
          e.preventDefault();
          if (canCheck) onAction('check', 0);
          else if (canCall) onAction('call', 0);
          break;
        case 'r':
          (document.querySelector('.raise-inp') as HTMLInputElement | null)?.focus();
          break;
        case 'a':
          if (canRaise) onAction('allin', 0);
          break;
      }
    };

    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [disabled, showCoach, canCheck, canCall, canRaise, onAction]);

  // ─── Pot odds ──────────────────────────────────────────────────────────────
  const potOdds = canCall && toCall > 0
    ? ((gameState.pot + toCall) / toCall).toFixed(1)
    : null;

  return (
    <div style={{
      width: '100%',
      display: 'flex',
      alignItems: 'flex-end',
      padding: '12px 8px 8px',
      gap: 8,
    }}>

      {/* ── Main action cluster (centered) ── */}
      <div style={{
        flex: 1,
        display: 'flex',
        gap: 10,
        justifyContent: 'center',
        flexWrap: 'wrap',
        alignItems: 'flex-end',
      }}>

      {/* ── FOLD ── */}
      <button
        className="abtn abtn-fold"
        disabled={disabled}
        onClick={() => onAction('fold', 0)}
      >
        FOLD<Hint k="F" />
      </button>

      {/* ── CHECK ── */}
      {canCheck && (
        <button
          className="abtn abtn-check"
          disabled={disabled}
          onClick={() => onAction('check', 0)}
        >
          CHECK<Hint k="C" />
        </button>
      )}

      {/* ── CALL + pot odds ── */}
      {canCall && (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 3 }}>
          <button
            className="abtn abtn-call"
            disabled={disabled}
            onClick={() => onAction('call', 0)}
          >
            CALL ${toCall}<Hint k="C" />
          </button>
          {potOdds && (
            <div style={{
              fontSize: 7,
              color: 'var(--gold-d)',
              fontFamily: 'var(--font-label)',
              letterSpacing: 1,
            }}>
              POT ODDS {potOdds}:1
            </div>
          )}
        </div>
      )}

      {/* ── RAISE area ── */}
      {canRaise && (
        <>
          {/* Quick-bet buttons */}
          <button
            className="abtn"
            style={{ fontSize: 9, padding: '7px 8px', borderColor: 'var(--gold-d)', color: 'var(--gold-d)' }}
            disabled={disabled}
            onClick={() => setQuickBet(Math.round(gameState.pot / 2))}
          >
            ½ POT
          </button>
          <button
            className="abtn"
            style={{ fontSize: 9, padding: '7px 8px', borderColor: 'var(--gold-d)', color: 'var(--gold-d)' }}
            disabled={disabled}
            onClick={() => setQuickBet(gameState.pot)}
          >
            POT
          </button>
          <button
            className="abtn"
            style={{ fontSize: 9, padding: '7px 8px', borderColor: 'var(--gold-d)', color: 'var(--gold-d)' }}
            disabled={disabled}
            onClick={() => setQuickBet(40)}
          >
            2×BB
          </button>

          {/* Decrement */}
          <button
            className="abtn"
            style={{ fontSize: 16, padding: '5px 12px', lineHeight: 1 }}
            disabled={disabled}
            onClick={() => adjustAmount(-step)}
          >
            ▼
          </button>

          {/* Amount input */}
          <input
            className="raise-inp"
            type="number"
            min={minRaise}
            max={maxRaise}
            placeholder={`$${minRaise}`}
            value={raiseAmount}
            onChange={e => setRaiseAmount(e.target.value)}
            disabled={disabled}
            onKeyDown={e => e.key === 'Enter' && handleRaise()}
          />

          {/* Increment */}
          <button
            className="abtn"
            style={{ fontSize: 16, padding: '5px 12px', lineHeight: 1 }}
            disabled={disabled}
            onClick={() => adjustAmount(step)}
          >
            ▲
          </button>

          {/* Step control: ◀ STEP N ▶ */}
          <button
            className="abtn"
            style={{ fontSize: 11, padding: '4px 8px', lineHeight: 1, borderColor: 'var(--gold-d)', color: 'var(--gold-d)' }}
            onClick={() => setStepIdx(i => (i - 1 + STEPS.length) % STEPS.length)}
          >
            ◀
          </button>
          <div style={{
            fontSize: 8,
            color: 'var(--gold-d)',
            fontFamily: 'var(--font-label)',
            alignSelf: 'center',
            whiteSpace: 'nowrap',
            letterSpacing: 1,
          }}>
            STEP {step}
          </div>
          <button
            className="abtn"
            style={{ fontSize: 11, padding: '4px 8px', lineHeight: 1, borderColor: 'var(--gold-d)', color: 'var(--gold-d)' }}
            onClick={() => setStepIdx(i => (i + 1) % STEPS.length)}
          >
            ▶
          </button>

          {/* Fix 8: min~max range hint */}
          <div style={{
            fontSize: 7,
            color: 'var(--gold-d)',
            fontFamily: 'var(--font-label)',
            textAlign: 'center',
            width: 110,
            alignSelf: 'center',
          }}>
            {minRaise}~{maxRaise}
          </div>

          {/* Raise confirm */}
          <button
            className="abtn abtn-raise"
            disabled={disabled || raiseAmount === ''}
            onClick={handleRaise}
          >
            RAISE ▲<Hint k="R" />
          </button>

        </>
      )}

      {/* ── ASK AI ── */}
      <button
        className="abtn abtn-ai"
        disabled={isRequestingAdvice}
        onClick={onAskAI}
      >
        {isRequestingAdvice ? '◈ THINKING...' : '◈ ASK AI'}
      </button>

      </div>{/* end main cluster */}

      {/* ── ALL IN — danger zone, far right ── */}
      {canRaise && (
        <button
          className="abtn"
          disabled={disabled}
          onClick={() => onAction('allin', 0)}
          style={{
            borderColor: '#aa2222',
            color: '#ff4444',
            fontSize: 7,
            padding: '6px 10px',
            flexShrink: 0,
            alignSelf: 'flex-end',
            lineHeight: 1.5,
          }}
        >
          ALL IN<br />${human?.chips}<Hint k="A" />
        </button>
      )}

    </div>
  );
};

export default ActionBar;

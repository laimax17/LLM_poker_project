import React, { useState, useEffect, useCallback } from 'react';
import type { GameState } from '../../types';
import { useT } from '../../i18n/I18nContext';

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
  const { t } = useT();
  const [raiseAmount, setRaiseAmount] = useState<string>('');
  const [stepIdx, setStepIdx] = useState(2); // default step = STEPS[2] = 10

  const human = gameState.players[0];
  const toCall = Math.max(0, gameState.current_bet - (human?.current_bet ?? 0));
  const minRaise = gameState.current_bet + gameState.min_raise;
  const maxRaise = human?.chips ?? 0;

  const canCheck = toCall === 0;
  const canCall = toCall > 0;
  const canRaise = maxRaise > toCall && (gameState.can_raise ?? true);

  const step = STEPS[stepIdx];
  const currentAmount = parseInt(raiseAmount, 10);
  const isOverMax = !isNaN(currentAmount) && currentAmount > maxRaise;

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
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;
      switch (e.key.toLowerCase()) {
        case 'f': onAction('fold', 0); break;
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

  // Shared small-button style for raise controls
  const smBtn: React.CSSProperties = { fontSize: 9, padding: '7px 8px', borderColor: 'var(--gold-d)', color: 'var(--gold-d)' };

  return (
    <div style={{
      width: '100%',
      padding: '10px 8px 6px',
      display: 'flex',
      flexDirection: 'column',
      gap: 6,
      flexShrink: 0,  // critical: prevent squishing the poker table above
    }}>

      {/* ══════ Row 1 — Main actions (always visible, fixed height) ══════ */}
      <div style={{
        display: 'flex',
        gap: 10,
        justifyContent: 'center',
        alignItems: 'stretch',   // stretch so all buttons share the same height
      }}>

        {/* FOLD */}
        <button
          className="abtn abtn-fold"
          style={{ height: 46 }}
          disabled={disabled}
          onClick={() => onAction('fold', 0)}
        >
          {t('action.fold')}<Hint k="F" />
        </button>

        {/* CHECK — two-line structure keeps height identical to CALL */}
        {canCheck && (
          <button
            className="abtn abtn-check"
            style={{ height: 46, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 2 }}
            disabled={disabled}
            onClick={() => onAction('check', 0)}
          >
            {t('action.check')}<Hint k="C" />
            {/* invisible spacer so height matches CALL+odds */}
            <span style={{ fontSize: 6, visibility: 'hidden' }}>0.0:1</span>
          </button>
        )}

        {/* CALL + pot odds */}
        {canCall && (
          <button
            className="abtn abtn-call"
            style={{ height: 46, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 2 }}
            disabled={disabled}
            onClick={() => onAction('call', 0)}
          >
            {t('action.call')} ${toCall}<Hint k="C" />
            <span style={{ fontSize: 6, visibility: potOdds ? 'visible' : 'hidden', color: 'var(--gold-d)' }}>
              {potOdds ?? '0.0'}:1 {t('bet.odds')}
            </span>
          </button>
        )}

        {/* ASK AI */}
        <button
          className="abtn abtn-ai"
          style={{ height: 46 }}
          disabled={isRequestingAdvice}
          onClick={onAskAI}
        >
          {isRequestingAdvice ? t('action.thinking') : t('action.askAi')}
        </button>

      </div>

      {/* ══════ Row 2 — Raise controls (fixed height slot, hidden when !canRaise) ══════ */}
      {/*
        Always takes up the same vertical space via height + visibility.
        This is the key fix: the table above is never pushed around by this row appearing/disappearing.
      */}
      <div style={{
        display: 'flex',
        gap: 8,
        justifyContent: 'center',
        alignItems: 'center',
        height: 46,
        visibility: canRaise ? 'visible' : 'hidden',
        flexWrap: 'nowrap',   // never wrap — width clips instead
        overflow: 'hidden',
      }}>

        {/* Quick-bet buttons */}
        <button className="abtn" style={smBtn} disabled={disabled}
          onClick={() => setQuickBet(Math.round(gameState.pot / 2))}>
          {t('bet.halfPot')}
        </button>
        <button className="abtn" style={smBtn} disabled={disabled}
          onClick={() => setQuickBet(gameState.pot)}>
          {t('bet.pot')}
        </button>
        <button className="abtn" style={smBtn} disabled={disabled}
          onClick={() => setQuickBet(40)}>
          {t('bet.2xbb')}
        </button>

        {/* Decrement */}
        <button className="abtn" style={{ fontSize: 14, padding: '4px 10px', lineHeight: 1 }}
          disabled={disabled} onClick={() => adjustAmount(-step)}>
          ▼
        </button>

        {/* Amount input */}
        <div style={{ position: 'relative' }}>
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
            style={{
              width: 90,
              padding: '10px 10px',
              borderColor: isOverMax ? '#ff4444' : undefined,
              outline: isOverMax ? '1px solid #ff4444' : undefined,
            }}
          />
          {isOverMax && (
            <div style={{
              position: 'absolute',
              top: '100%',
              left: 0,
              fontSize: 7,
              color: '#ff4444',
              fontFamily: 'var(--font-label)',
              whiteSpace: 'nowrap',
              marginTop: 2,
            }}>
              Max ${maxRaise}
            </div>
          )}
        </div>

        {/* Increment */}
        <button className="abtn" style={{ fontSize: 14, padding: '4px 10px', lineHeight: 1 }}
          disabled={disabled} onClick={() => adjustAmount(step)}>
          ▲
        </button>

        {/* Step selector */}
        <button className="abtn" style={{ fontSize: 10, padding: '4px 6px', lineHeight: 1, borderColor: 'var(--gold-d)', color: 'var(--gold-d)' }}
          onClick={() => setStepIdx(i => (i - 1 + STEPS.length) % STEPS.length)}>
          ◀
        </button>
        <div style={{ fontSize: 7, color: 'var(--gold-d)', fontFamily: 'var(--font-label)', whiteSpace: 'nowrap', letterSpacing: 1 }}>
          {t('bet.step')} {step}
        </div>
        <button className="abtn" style={{ fontSize: 10, padding: '4px 6px', lineHeight: 1, borderColor: 'var(--gold-d)', color: 'var(--gold-d)' }}
          onClick={() => setStepIdx(i => (i + 1) % STEPS.length)}>
          ▶
        </button>

        {/* Range hint */}
        <div style={{ fontSize: 7, color: 'var(--gold-d)', fontFamily: 'var(--font-label)', whiteSpace: 'nowrap', letterSpacing: 1 }}>
          {minRaise}~{maxRaise}
        </div>

        {/* RAISE confirm */}
        <button
          className="abtn abtn-raise"
          disabled={disabled || raiseAmount === ''}
          onClick={handleRaise}
        >
          {t('action.raise')} ▲<Hint k="R" />
        </button>

        {/* ALL IN */}
        <button
          className="abtn"
          disabled={disabled}
          onClick={() => onAction('allin', 0)}
          style={{ borderColor: '#aa2222', color: '#ff4444', fontSize: 7, padding: '4px 10px', lineHeight: 1.5 }}
        >
          {t('action.allin')}<br />${human?.chips}<Hint k="A" />
        </button>

      </div>

    </div>
  );
};

export default ActionBar;

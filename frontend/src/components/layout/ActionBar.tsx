import React, { useState } from 'react';
import type { GameState } from '../../types';

interface ActionBarProps {
  gameState: GameState;
  onAction: (action: string, amount: number) => void;
  onAskAI: () => void;
  isRequestingAdvice: boolean;
  disabled: boolean;
}

const ActionBar: React.FC<ActionBarProps> = ({
  gameState,
  onAction,
  onAskAI,
  isRequestingAdvice,
  disabled,
}) => {
  const [raiseAmount, setRaiseAmount] = useState<string>('');

  const human = gameState.players[0];
  const toCall = Math.max(0, gameState.current_bet - (human?.current_bet ?? 0));
  const minRaise = gameState.current_bet + gameState.min_raise;
  const maxRaise = human?.chips ?? 0;

  const canCheck = toCall === 0;
  const canCall = toCall > 0;
  const canRaise = maxRaise > toCall;

  function handleRaise() {
    const amt = parseInt(raiseAmount, 10);
    if (isNaN(amt)) return;
    const clamped = Math.max(minRaise, Math.min(maxRaise, amt));
    onAction('raise', clamped);
    setRaiseAmount('');
  }

  function handleRaiseInput(e: React.ChangeEvent<HTMLInputElement>) {
    const val = e.target.value;
    setRaiseAmount(val);
  }

  return (
    <div style={{
      width: '100%',
      maxWidth: 960,
      display: 'flex',
      gap: 8,
      justifyContent: 'center',
      flexWrap: 'wrap',
      padding: '16px 16px 10px',
    }}>
      {/* FOLD */}
      <button
        className="abtn abtn-fold"
        disabled={disabled}
        onClick={() => onAction('fold', 0)}
      >
        FOLD
      </button>

      {/* CHECK */}
      {canCheck && (
        <button
          className="abtn abtn-check"
          disabled={disabled}
          onClick={() => onAction('check', 0)}
        >
          CHECK
        </button>
      )}

      {/* CALL */}
      {canCall && (
        <button
          className="abtn abtn-call"
          disabled={disabled}
          onClick={() => onAction('call', 0)}
        >
          CALL ${toCall}
        </button>
      )}

      {/* RAISE input + button */}
      {canRaise && (
        <>
          <input
            className="raise-inp"
            type="number"
            min={minRaise}
            max={maxRaise}
            placeholder={`$${minRaise}`}
            value={raiseAmount}
            onChange={handleRaiseInput}
            disabled={disabled}
            onKeyDown={e => e.key === 'Enter' && handleRaise()}
          />
          <button
            className="abtn abtn-raise"
            disabled={disabled || raiseAmount === ''}
            onClick={handleRaise}
          >
            RAISE ▲
          </button>
        </>
      )}

      {/* ASK AI */}
      <button
        className="abtn abtn-ai"
        disabled={isRequestingAdvice}
        onClick={onAskAI}
      >
        {isRequestingAdvice ? '◈ THINKING...' : '◈ ASK AI'}
      </button>
    </div>
  );
};

export default ActionBar;

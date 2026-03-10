import React, { useState, useRef } from 'react';
import type { LLMConfig } from '../../types';
import { setSoundEnabled } from '../../utils/sound';

interface LLMConfigBarProps {
  config: LLMConfig;
  onConfigChange: (config: Partial<LLMConfig>) => void;
}

const labelStyle: React.CSSProperties = {
  fontSize: 7,
  color: 'var(--gold-d)',
  letterSpacing: 1,
  fontFamily: 'var(--font-label)',
};

const LLMConfigBar: React.FC<LLMConfigBarProps> = ({ config, onConfigChange }) => {
  const isOnline = config.status === 'online';
  const [soundOn, setSoundOn] = useState(true);
  const inputRef = useRef<HTMLInputElement>(null);

  function toggleSound() {
    const next = !soundOn;
    setSoundOn(next);
    setSoundEnabled(next);
  }

  function commitModel() {
    const val = inputRef.current?.value.trim() ?? '';
    if (val && val !== config.model) {
      onConfigChange({ model: val });
    }
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter') {
      commitModel();
      inputRef.current?.blur();
    }
  }

  return (
    <div style={{
      width: '100%',
      padding: '0 8px 14px',
    }}>
      <div style={{
        background: 'var(--surface)',
        border: '2px solid var(--brown)',
        padding: '9px 14px',
        display: 'flex',
        alignItems: 'center',
        gap: 12,
        flexWrap: 'wrap',
      }}>
        {/* Provider label */}
        <span style={labelStyle}>OPENROUTER</span>

        {/* Model input */}
        <span style={labelStyle}>MODEL</span>
        <input
          ref={inputRef}
          type="text"
          defaultValue={config.model}
          placeholder="e.g. google/gemma-2-9b-it:free"
          onBlur={commitModel}
          onKeyDown={handleKeyDown}
          style={{
            fontFamily: 'var(--font-label)',
            fontSize: 7,
            background: '#000',
            border: '2px solid var(--brown)',
            color: 'var(--gold)',
            padding: '5px 8px',
            outline: 'none',
            minWidth: 200,
          }}
        />

        {/* SFX toggle + Status (pushed to right) */}
        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 10 }}>
          <button
            onClick={toggleSound}
            style={{
              ...labelStyle,
              cursor: 'pointer',
              background: 'none',
              border: 'none',
              color: soundOn ? 'var(--gold)' : 'var(--gold-d)',
              padding: 0,
            }}
          >
            {soundOn ? '♪ SFX' : '✕ SFX'}
          </button>

          {/* Status dot + text */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <div style={{
              display: 'inline-block',
              width: 6,
              height: 6,
              background: isOnline ? '#44cc66' : '#cc4444',
              boxShadow: isOnline ? '0 0 5px #44cc66' : 'none',
              animation: isOnline ? 'status-dot-pulse 1.2s steps(1) infinite' : 'none',
            }} />
            <span style={{
              fontSize: 7,
              color: isOnline ? '#44cc66' : '#cc4444',
              fontFamily: 'var(--font-label)',
            }}>
              {config.status === 'loading' ? 'CONNECTING...' : isOnline ? 'ONLINE' : 'OFFLINE'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LLMConfigBar;

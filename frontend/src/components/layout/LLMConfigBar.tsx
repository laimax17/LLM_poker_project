import React from 'react';
import type { LLMConfig, LLMEngine } from '../../types';

interface LLMConfigBarProps {
  config: LLMConfig;
  onConfigChange: (config: Partial<LLMConfig>) => void;
}

const OLLAMA_MODELS = ['qwen2.5:7b', 'qwen2.5:14b', 'llama3.1:8b'];

const ENGINE_OPTIONS: { value: LLMEngine; label: string }[] = [
  { value: 'rule-based', label: 'RULE-BASED' },
  { value: 'ollama',     label: 'OLLAMA' },
  { value: 'qwen-plus',  label: 'QWEN-PLUS' },
  { value: 'qwen-max',   label: 'QWEN-MAX' },
];

const selectStyle: React.CSSProperties = {
  fontFamily: 'var(--font-label)',
  fontSize: 7,
  background: '#000',
  border: '2px solid var(--brown)',
  color: 'var(--gold)',
  padding: '5px 8px',
  cursor: 'pointer',
  outline: 'none',
};

const labelStyle: React.CSSProperties = {
  fontSize: 7,
  color: 'var(--gold-d)',
  letterSpacing: 1,
  fontFamily: 'var(--font-label)',
};

const LLMConfigBar: React.FC<LLMConfigBarProps> = ({ config, onConfigChange }) => {
  const showModelSelect = config.engine === 'ollama';
  const isOnline = config.status === 'online';

  function handleEngineChange(e: React.ChangeEvent<HTMLSelectElement>) {
    const engine = e.target.value as LLMEngine;
    let model = config.model;
    if (engine === 'ollama') model = OLLAMA_MODELS[0];
    else if (engine === 'qwen-plus') model = 'qwen-plus';
    else if (engine === 'qwen-max') model = 'qwen-max';
    else model = '';
    onConfigChange({ engine, model });
  }

  function handleModelChange(e: React.ChangeEvent<HTMLSelectElement>) {
    onConfigChange({ model: e.target.value });
  }

  return (
    <div style={{
      width: '100%',
      maxWidth: 1100,
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
        {/* Label */}
        <span style={labelStyle}>AI ENGINE</span>

        {/* Engine select */}
        <select
          style={selectStyle}
          value={config.engine}
          onChange={handleEngineChange}
        >
          {ENGINE_OPTIONS.map(opt => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>

        {/* Model select — only for Ollama */}
        {showModelSelect && (
          <>
            <span style={labelStyle}>MODEL</span>
            <select
              style={selectStyle}
              value={config.model}
              onChange={handleModelChange}
            >
              {OLLAMA_MODELS.map(m => (
                <option key={m} value={m}>{m}</option>
              ))}
            </select>
          </>
        )}

        {/* Qwen model info (static) */}
        {(config.engine === 'qwen-plus' || config.engine === 'qwen-max') && (
          <span style={{ ...labelStyle, color: 'var(--gold-d)' }}>
            MODEL: {config.engine}
          </span>
        )}

        {/* Status dot + text (right-aligned) */}
        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 6 }}>
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
  );
};

export default LLMConfigBar;

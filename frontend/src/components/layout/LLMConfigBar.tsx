import React, { useEffect, useState } from 'react';
import type { LLMConfig, LLMEngine, ModelsRegistry } from '../../types';
import { setSoundEnabled } from '../../utils/sound';
import { useT } from '../../i18n/I18nContext';

interface LLMConfigBarProps {
  config: LLMConfig;
  onConfigChange: (config: Partial<LLMConfig>) => void;
  learningMode: boolean;
  onLearningModeChange: (enabled: boolean) => void;
  onToggleStats: () => void;
}

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL ?? 'http://localhost:8000';

// Offline engines that need no provider/model.
const OFFLINE_ENGINES: { value: LLMEngine; label: string }[] = [
  { value: 'rule-based', label: 'RULE-BASED' },
  { value: 'gto', label: 'GTO' },
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

const LLMConfigBar: React.FC<LLMConfigBarProps> = ({
  config,
  onConfigChange,
  learningMode,
  onLearningModeChange,
  onToggleStats,
}) => {
  const { t } = useT();
  const isOnline = config.status === 'online';
  const [soundOn, setSoundOn] = useState(true);
  const [registry, setRegistry] = useState<ModelsRegistry | null>(null);

  // Fetch the provider/model registry once.
  useEffect(() => {
    fetch(`${BACKEND_URL}/ai/models`)
      .then((r) => r.json())
      .then((data: ModelsRegistry) => setRegistry(data))
      .catch(() => setRegistry(null));
  }, []);

  function toggleSound() {
    const next = !soundOn;
    setSoundOn(next);
    setSoundEnabled(next);
  }

  // Models available for the currently-selected engine (provider).
  const modelsForEngine =
    registry?.models.filter((m) => m.provider === config.engine) ?? [];
  const isLLMEngine = modelsForEngine.length > 0;

  function handleEngineChange(e: React.ChangeEvent<HTMLSelectElement>) {
    const engine = e.target.value as LLMEngine;
    // When switching to an LLM provider, pick its first model (or default).
    const provider = registry?.providers.find((p) => p.id === engine);
    const firstModel = registry?.models.find((m) => m.provider === engine);
    const model = provider?.defaultModel || firstModel?.id || '';
    onConfigChange({ engine, model });
  }

  function handleModelChange(e: React.ChangeEvent<HTMLSelectElement>) {
    onConfigChange({ model: e.target.value });
  }

  return (
    <div style={{ width: '100%', padding: '0 8px 14px' }}>
      <div
        style={{
          background: 'var(--surface)',
          border: '2px solid var(--brown)',
          padding: '9px 14px',
          display: 'flex',
          alignItems: 'center',
          gap: 12,
          flexWrap: 'wrap',
        }}
      >
        {/* Label */}
        <span style={labelStyle}>AI ENGINE</span>

        {/* Engine / provider select */}
        <select style={selectStyle} value={config.engine} onChange={handleEngineChange}>
          {OFFLINE_ENGINES.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
          {registry?.providers.map((p) => (
            <option key={p.id} value={p.id}>
              {p.label.toUpperCase()}
              {p.available ? '' : ' (NO KEY)'}
            </option>
          ))}
        </select>

        {/* Model select — for any LLM provider */}
        {isLLMEngine && (
          <>
            <span style={labelStyle}>MODEL</span>
            <select style={selectStyle} value={config.model} onChange={handleModelChange}>
              {modelsForEngine.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.label}
                </option>
              ))}
            </select>
          </>
        )}

        {/* Learning mode + stats + SFX toggle */}
        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 10 }}>
          <button
            onClick={() => onLearningModeChange(!learningMode)}
            style={{
              ...labelStyle,
              cursor: 'pointer',
              background: 'none',
              border: `1px solid ${learningMode ? 'var(--gold)' : 'var(--brown)'}`,
              color: learningMode ? 'var(--gold)' : 'var(--gold-d)',
              padding: '4px 7px',
            }}
          >
            {learningMode ? '◉' : '○'} {t('learn.toggle')}
          </button>

          {learningMode && (
            <button
              onClick={onToggleStats}
              style={{
                ...labelStyle,
                cursor: 'pointer',
                background: 'none',
                border: '1px solid var(--brown)',
                color: 'var(--gold-d)',
                padding: '4px 7px',
              }}
            >
              {t('learn.statsBtn')}
            </button>
          )}

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
            <div
              style={{
                display: 'inline-block',
                width: 6,
                height: 6,
                background: isOnline ? '#44cc66' : '#cc4444',
                boxShadow: isOnline ? '0 0 5px #44cc66' : 'none',
                animation: isOnline ? 'status-dot-pulse 1.2s steps(1) infinite' : 'none',
              }}
            />
            <span
              style={{
                fontSize: 7,
                color: isOnline ? '#44cc66' : '#cc4444',
                fontFamily: 'var(--font-label)',
              }}
            >
              {config.status === 'loading'
                ? 'CONNECTING...'
                : isOnline
                ? 'ONLINE'
                : 'OFFLINE'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LLMConfigBar;

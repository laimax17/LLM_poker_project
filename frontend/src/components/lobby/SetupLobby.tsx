import React, { useState } from 'react';
import type { GameSetupConfig } from '../../types';
import { useT } from '../../i18n/I18nContext';

interface SetupLobbyProps {
  onStart: (config: GameSetupConfig) => void;
}

const labelStyle: React.CSSProperties = {
  fontSize: 8,
  color: 'var(--gold-d)',
  letterSpacing: 1,
  fontFamily: 'var(--font-label)',
  marginBottom: 8,
};

function OptionRow<T extends string | number>({
  label,
  options,
  value,
  onChange,
}: {
  label: string;
  options: { v: T; l: string }[];
  value: T;
  onChange: (v: T) => void;
}) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
      <div style={labelStyle}>{label}</div>
      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', justifyContent: 'center' }}>
        {options.map((o) => {
          const active = o.v === value;
          return (
            <button
              key={String(o.v)}
              onClick={() => onChange(o.v)}
              style={{
                background: active ? 'var(--gold)' : 'transparent',
                border: `2px solid ${active ? 'var(--gold)' : 'var(--brown)'}`,
                color: active ? '#000' : 'var(--gold)',
                fontSize: 8,
                padding: '7px 12px',
                cursor: 'pointer',
                fontFamily: 'var(--font-label)',
                letterSpacing: 1,
              }}
            >
              {o.l}
            </button>
          );
        })}
      </div>
    </div>
  );
}

const SetupLobby: React.FC<SetupLobbyProps> = ({ onStart }) => {
  const { t } = useT();
  const [numOpponents, setNumOpponents] = useState(5);
  const [stack, setStack] = useState(5000);
  const [speed, setSpeed] = useState<'turbo' | 'normal' | 'slow'>('normal');
  const [difficulty, setDifficulty] = useState<'easy' | 'normal' | 'hard'>('normal');

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: 18,
        marginTop: 8,
        width: '100%',
        maxWidth: 520,
      }}
    >
      <OptionRow
        label={t('setup.opponents')}
        value={numOpponents}
        onChange={setNumOpponents}
        options={[1, 2, 3, 4, 5].map((n) => ({ v: n, l: String(n) }))}
      />
      <OptionRow
        label={t('setup.stack')}
        value={stack}
        onChange={setStack}
        options={[
          { v: 2000, l: '2K' },
          { v: 5000, l: '5K' },
          { v: 10000, l: '10K' },
        ]}
      />
      <OptionRow
        label={t('setup.speed')}
        value={speed}
        onChange={setSpeed}
        options={[
          { v: 'turbo', l: t('setup.speed.turbo') },
          { v: 'normal', l: t('setup.speed.normal') },
          { v: 'slow', l: t('setup.speed.slow') },
        ]}
      />
      <OptionRow
        label={t('setup.difficulty')}
        value={difficulty}
        onChange={setDifficulty}
        options={[
          { v: 'easy', l: t('setup.diff.easy') },
          { v: 'normal', l: t('setup.diff.normal') },
          { v: 'hard', l: t('setup.diff.hard') },
        ]}
      />

      <button
        className="abtn abtn-raise"
        style={{ fontSize: 13, padding: '16px 32px', marginTop: 8 }}
        onClick={() =>
          onStart({
            num_opponents: numOpponents,
            starting_stack: stack,
            blind_speed: speed,
            difficulty,
          })
        }
      >
        {t('app.start')}
      </button>
    </div>
  );
};

export default SetupLobby;

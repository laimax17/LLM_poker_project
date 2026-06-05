import React from 'react';

interface PotDisplayProps {
  pot: number;
}

const PotDisplay: React.FC<PotDisplayProps> = ({ pot }) => {
  return (
    <div
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 12,
        background: 'rgba(8,12,10,0.92)',
        border: '1px solid rgba(231,194,100,0.45)',
        borderRadius: 24,
        padding: '8px 22px',
        boxShadow: '0 4px 12px rgba(0,0,0,0.4)',
      }}
    >
      <span
        style={{
          width: 18,
          height: 18,
          borderRadius: '50%',
          background: 'radial-gradient(circle at 35% 35%, var(--gold-l), var(--gold-d))',
          border: '2px solid #1a1208',
          flexShrink: 0,
        }}
      />
      <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-dim)', letterSpacing: 1 }}>POT</span>
      <span
        key={pot}
        style={{
          fontFamily: 'var(--font-ui)',
          fontSize: 26,
          fontWeight: 700,
          color: 'var(--gold-l)',
          animation: 'numUpdate 0.4s ease-out',
        }}
      >
        {pot.toLocaleString()}
      </span>
    </div>
  );
};

export default PotDisplay;

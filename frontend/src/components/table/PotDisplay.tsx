import React from 'react';

interface PotDisplayProps {
  pot: number;
  street: string;
}

const PotDisplay: React.FC<PotDisplayProps> = ({ pot, street }) => {
  return (
    <div style={{ textAlign: 'center' }}>
      {/* Street label */}
      <div style={{
        fontSize: 7,
        color: 'var(--gold-d)',
        letterSpacing: 3,
        marginBottom: 4,
        fontFamily: 'var(--font-label)',
      }}>
        {street}
      </div>
      {/* Pot amount — key changes force animation replay when pot grows */}
      <div style={{
        fontSize: 10,
        color: 'var(--gold-l)',
        letterSpacing: 2,
        textShadow: '0 0 6px var(--gold)',
        fontFamily: 'var(--font-label)',
        whiteSpace: 'nowrap',
      }}>
        ◈ POT :{' '}
        <span
          key={pot}
          style={{ display: 'inline-block', animation: 'numUpdate 0.4s ease-out' }}
        >
          ${pot.toLocaleString()}
        </span>
        {' '}◈
      </div>
    </div>
  );
};

export default PotDisplay;

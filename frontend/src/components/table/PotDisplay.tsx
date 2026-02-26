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
      {/* Pot amount */}
      <div style={{
        fontSize: 10,
        color: 'var(--gold-l)',
        letterSpacing: 2,
        textShadow: '0 0 6px var(--gold)',
        fontFamily: 'var(--font-label)',
        whiteSpace: 'nowrap',
      }}>
        ◈ POT : ${pot.toLocaleString()} ◈
      </div>
    </div>
  );
};

export default PotDisplay;

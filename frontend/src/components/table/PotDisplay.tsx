import React, { useRef, useEffect, useState } from 'react';
import ChipStack from './ChipStack';

interface PotDisplayProps {
  pot: number;
  street: string;
}

const PotDisplay: React.FC<PotDisplayProps> = ({ pot, street }) => {
  // Track whether the pot just grew so we can apply the glow animation
  const prevPot = useRef(pot);
  const [glowing, setGlowing] = useState(false);

  useEffect(() => {
    if (pot > prevPot.current) {
      setGlowing(true);
      const t = setTimeout(() => setGlowing(false), 600);
      prevPot.current = pot;
      return () => clearTimeout(t);
    }
    prevPot.current = pot;
  }, [pot]);

  return (
    <div style={{ textAlign: 'center' }}>
      {/* Street label */}
      <div style={{
        fontSize: 7,
        color: 'var(--gold-d)',
        letterSpacing: 3,
        marginBottom: 6,
        fontFamily: 'var(--font-label)',
      }}>
        {street}
      </div>

      {/* Chip stack visual — key forces remount+animation on every pot change */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'center',
          marginBottom: 8,
          minHeight: 40,        // reserve space so layout doesn't jump at 0
          alignItems: 'flex-end',
          animation: glowing ? 'chipGlow 0.6s ease-out' : 'none',
        }}
      >
        <ChipStack key={pot} amount={pot} size="md" />
      </div>

      {/* Pot amount text */}
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

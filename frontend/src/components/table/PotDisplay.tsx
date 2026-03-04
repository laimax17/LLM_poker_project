import React, { useRef, useEffect, useState } from 'react';
import ChipStack from './ChipStack';
import { useT } from '../../i18n/I18nContext';

interface PotDisplayProps {
  pot: number;
  street: string;
}

const PotDisplay: React.FC<PotDisplayProps> = ({ pot, street }) => {
  const { t } = useT();
  const prevPot = useRef(pot);
  const [glowing, setGlowing] = useState(false);
  // When pot drops to 0 (winner awarded), briefly show old value with chipCollect animation
  const [collecting, setCollecting] = useState(false);
  const [collectingAmount, setCollectingAmount] = useState(0);

  useEffect(() => {
    if (pot === 0 && prevPot.current > 0) {
      // Pot was just awarded — animate chips flying away before disappearing
      setCollectingAmount(prevPot.current);
      setCollecting(true);
      const timer = setTimeout(() => setCollecting(false), 550);
      prevPot.current = 0;
      return () => clearTimeout(timer);
    }
    if (pot > prevPot.current) {
      setGlowing(true);
      const timer = setTimeout(() => setGlowing(false), 600);
      prevPot.current = pot;
      return () => clearTimeout(timer);
    }
    prevPot.current = pot;
  }, [pot]);

  const displayPot = collecting ? collectingAmount : pot;

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

      {/* Chip stack visual */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'center',
          marginBottom: 8,
          minHeight: 40,
          alignItems: 'flex-end',
          animation: collecting
            ? 'chipCollect 0.5s ease-in forwards'
            : glowing ? 'chipGlow 0.6s ease-out' : 'none',
        }}
      >
        <ChipStack key={displayPot} amount={displayPot} size="md" />
      </div>

      {/* Pot amount text — fades out during collection */}
      <div style={{
        fontSize: 10,
        color: 'var(--gold-l)',
        letterSpacing: 2,
        textShadow: '0 0 6px var(--gold)',
        fontFamily: 'var(--font-label)',
        whiteSpace: 'nowrap',
        opacity: collecting ? 0 : 1,
        transition: collecting ? 'opacity 0.3s ease' : 'none',
      }}>
        {t('pot.label')}{' '}
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

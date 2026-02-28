import React from 'react';

interface ChipStackProps {
  /** Chip amount to represent visually */
  amount: number;
  /** 'sm' for small contexts, 'md' for pot display, 'lg' for enlarged bot bet bubbles */
  size?: 'sm' | 'md' | 'lg';
}

/**
 * Map a chip amount to the number of visual chips to show.
 * Uses a logarithmic-ish curve so small amounts get 1-2 chips
 * and large pots get a satisfying tall stack.
 */
function getChipCount(amount: number): number {
  if (amount <= 0)    return 0;
  if (amount <= 20)   return 1;
  if (amount <= 60)   return 2;
  if (amount <= 150)  return 3;
  if (amount <= 350)  return 4;
  if (amount <= 700)  return 5;
  if (amount <= 1500) return 6;
  if (amount <= 3000) return 7;
  if (amount <= 6000) return 8;
  return 9;
}

/**
 * Each entry defines the gradient colors for one chip layer.
 * Chips alternate through this palette bottom→top.
 */
const PALETTE: Array<{ top: string; mid: string; bot: string }> = [
  { top: '#e8d080', mid: '#c8a040', bot: '#7a5018' }, // bright gold
  { top: '#c8a040', mid: '#a08030', bot: '#5a3a10' }, // dark gold
  { top: '#f0d888', mid: '#d4b040', bot: '#8b6020' }, // light gold
  { top: '#d4b050', mid: '#b09030', bot: '#6a4c14' }, // medium gold
  { top: '#e0c060', mid: '#c09020', bot: '#6b5010' }, // warm gold
];

const ChipStack: React.FC<ChipStackProps> = ({ amount, size = 'md' }) => {
  const count = getChipCount(amount);
  if (count === 0) return null;

  const W = size === 'lg' ? 52 : size === 'sm' ? 28 : 36;  // chip width px
  const H = size === 'lg' ? 14 : size === 'sm' ? 7  : 10;  // chip height px
  const OVERLAP = size === 'lg' ? -6 : size === 'sm' ? -3  : -4; // negative margin to stack chips

  return (
    <div
      style={{
        display: 'inline-flex',
        // column-reverse: chip index 0 renders at the bottom of the stack
        flexDirection: 'column-reverse',
        alignItems: 'center',
      }}
    >
      {Array.from({ length: count }, (_, i) => {
        const p = PALETTE[i % PALETTE.length];
        const isTop = i === count - 1;
        const delay = `${i * 0.045}s`;

        return (
          <div
            key={i}
            style={{
              width: W,
              height: H,
              borderRadius: H / 2,
              // Top-to-bottom gradient for a 3-D cylinder look
              background: `linear-gradient(to bottom,
                ${p.top} 0%,
                ${p.mid} 40%,
                ${p.mid} 65%,
                ${p.bot} 100%)`,
              border: `1px solid ${p.bot}`,
              boxShadow: isTop
                ? `0 2px 5px rgba(0,0,0,0.7), 0 0 8px rgba(200,160,64,0.4)`
                : `0 1px 3px rgba(0,0,0,0.5)`,
              marginTop: i > 0 ? OVERLAP : 0,
              // stagger animation per chip layer
              animation: `chipIn 0.22s ease-out ${delay} both`,
            }}
          />
        );
      })}
    </div>
  );
};

export default ChipStack;

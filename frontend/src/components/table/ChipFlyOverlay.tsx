import React from 'react';
import { useGameStore } from '../../store/useGameStore';

/**
 * Approximate player positions (% of table container) — after clockwise fix:
 *   Top→bottom left column = players[3], [2], [1]
 *   Top→bottom right column = players[4], [5]
 *   Bottom center = player[0] (human)
 */
const PLAYER_POS: Record<number, { x: number; y: number }> = {
  0: { x: 50, y: 82 },   // human — bottom center
  1: { x: 18, y: 75 },   // bot-left bottom (clockwise pos 1)
  2: { x: 18, y: 50 },   // bot-left mid    (clockwise pos 2)
  3: { x: 18, y: 25 },   // bot-left top    (clockwise pos 3)
  4: { x: 82, y: 25 },   // bot-right top   (clockwise pos 4)
  5: { x: 82, y: 50 },   // bot-right mid   (clockwise pos 5)
};

const POT_POS = { x: 50, y: 42 };

const ChipFlyOverlay: React.FC = () => {
  const triggers = useGameStore(s => s.chipFlyTriggers);
  const removeChipFly = useGameStore(s => s.removeChipFly);

  if (triggers.length === 0) return null;

  return (
    <div style={{
      position: 'absolute',
      inset: 0,
      pointerEvents: 'none',
      zIndex: 5,
      overflow: 'hidden',
      containerType: 'size',
    }}>
      {triggers.map(t => {
        const from = PLAYER_POS[t.fromPlayerIdx] ?? POT_POS;
        const dx = POT_POS.x - from.x;
        const dy = POT_POS.y - from.y;

        return (
          <div
            key={t.id}
            style={{
              position: 'absolute',
              left: `${from.x}%`,
              top: `${from.y}%`,
              transform: 'translate(-50%, -50%)',
              // CSS custom properties for the animation endpoint
              '--fly-dx': `${dx}cqw`,
              '--fly-dy': `${dy}cqh`,
            } as React.CSSProperties}
          >
            {/* Chip stack visual — 1-3 chips based on amount */}
            <div
              onAnimationEnd={() => removeChipFly(t.id)}
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: 0,
                animation: 'chipFly 0.45s ease-in forwards',
              }}
            >
              {Array.from({ length: Math.min(3, Math.max(1, Math.ceil(t.amount / 100))) }).map((_, i) => (
                <div
                  key={i}
                  style={{
                    width: 16,
                    height: 10,
                    borderRadius: '50%',
                    background: 'linear-gradient(135deg, #e8d080 0%, #c8a040 50%, #6b4c10 100%)',
                    border: '1px solid #6b4c10',
                    boxShadow: '0 1px 2px rgba(0,0,0,0.5)',
                    marginTop: i > 0 ? -6 : 0,
                  }}
                />
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default ChipFlyOverlay;

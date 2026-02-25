import React from 'react';
import { rankToDisplay, suitToSymbol, isRedSuit } from '../../utils/cardDisplay';

export type CardSize = 'lg' | 'md' | 'sm' | 'xs';
export type CardGlow = 'gold' | 'red' | 'none';
export type CardVariant = 'face-up' | 'face-down' | 'placeholder';

interface CardProps {
  size: CardSize;
  variant?: CardVariant;
  rank?: number;
  suit?: string;
  glow?: CardGlow;
  className?: string;
}

interface SizeSpec {
  width: number;
  height: number;
  clipPx: number;
  shadow: string;
  rankFontSize: number;
  suitFontSize: number;    // center suit (LG/MD/SM) or br-suit (XS)
  tlTop: number;
  tlLeft: number;
  borderWidth: number;
}

const SIZES: Record<CardSize, SizeSpec> = {
  // Dimensions from design_reference/layout_v3.html
  lg: {
    width: 62, height: 88,
    clipPx: 5,
    shadow: '3px 3px 0 #000',
    rankFontSize: 20,
    suitFontSize: 40,
    tlTop: 5, tlLeft: 6,
    borderWidth: 3,
  },
  md: {
    width: 58, height: 82,
    clipPx: 5,
    shadow: '3px 3px 0 #000',
    rankFontSize: 18,
    suitFontSize: 36,
    tlTop: 5, tlLeft: 6,
    borderWidth: 3,
  },
  sm: {
    width: 30, height: 42,
    clipPx: 3,
    shadow: '1px 1px 0 #000',
    rankFontSize: 10,
    suitFontSize: 16,
    tlTop: 3, tlLeft: 4,
    borderWidth: 2,
  },
  xs: {
    width: 30, height: 40,
    clipPx: 3,
    shadow: '1px 1px 0 #000',
    rankFontSize: 11,
    suitFontSize: 13,
    tlTop: 3, tlLeft: 4,
    borderWidth: 2,
  },
};

function makeClipPath(px: number): string {
  return `polygon(${px}px 0%, calc(100% - ${px}px) 0%, 100% ${px}px, 100% calc(100% - ${px}px), calc(100% - ${px}px) 100%, ${px}px 100%, 0% calc(100% - ${px}px), 0% ${px}px)`;
}

function getBoxShadow(size: CardSize, glow: CardGlow, variant: CardVariant): string {
  if (variant === 'placeholder') return 'none';
  const base = SIZES[size].shadow;
  if (glow === 'gold') return `${base}, 0 0 18px rgba(200,160,64,0.55)`;
  if (glow === 'red')  return `${base}, 0 0 16px rgba(204,17,17,0.4)`;
  return base;
}

function getBorderColor(glow: CardGlow, variant: CardVariant): string {
  if (variant === 'face-down') return 'var(--card-back-border)';
  if (variant === 'placeholder') return 'var(--card-back-border)';
  if (glow === 'gold') return 'var(--gold)';
  if (glow === 'red')  return 'var(--red)';
  return 'var(--card-border)';
}

const Card: React.FC<CardProps> = ({
  size,
  variant = 'face-up',
  rank,
  suit,
  glow = 'none',
  className = '',
}) => {
  const spec = SIZES[size];
  const isXS = size === 'xs';
  const redSuit = suit ? isRedSuit(suit) : false;
  const suitColor = redSuit ? 'var(--red)' : 'var(--black)';

  // XS: inline-flex for embedding in text
  const xsInlineStyle: React.CSSProperties = isXS
    ? { display: 'inline-flex', verticalAlign: 'middle', position: 'relative', top: -2, margin: '0 2px' }
    : {};

  const rootStyle: React.CSSProperties = {
    width: spec.width,
    height: spec.height,
    position: 'relative',
    flexShrink: 0,
    clipPath: makeClipPath(spec.clipPx),
    border: `${spec.borderWidth}px solid ${getBorderColor(glow, variant)}`,
    boxShadow: getBoxShadow(size, glow, variant),
    background: variant === 'face-down'
      ? 'var(--card-back-bg)'
      : variant === 'placeholder'
        ? 'transparent'
        : 'var(--card-bg)',
    borderStyle: variant === 'placeholder' ? 'dashed' : 'solid',
    opacity: variant === 'placeholder' ? 0.2 : 1,
    overflow: 'hidden',
    ...xsInlineStyle,
  };

  // === PLACEHOLDER ===
  if (variant === 'placeholder') {
    return (
      <div style={rootStyle} className={className}>
        <div style={{
          position: 'absolute', inset: 0,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <span style={{
            fontSize: size === 'lg' ? 22 : size === 'md' ? 22 : 12,
            color: '#2a4a2a',
            fontFamily: 'Georgia, serif',
            fontWeight: 900,
            userSelect: 'none',
          }}>?</span>
        </div>
      </div>
    );
  }

  // === FACE-DOWN ===
  if (variant === 'face-down') {
    return (
      <div style={rootStyle} className={className}>
        {/* Crosshatch inset pattern */}
        <div style={{
          position: 'absolute',
          inset: 5,
          border: '1px solid rgba(200,160,64,0.2)',
          backgroundImage: [
            'repeating-linear-gradient(45deg, rgba(200,160,64,0.07) 0, rgba(200,160,64,0.07) 1px, transparent 1px, transparent 8px)',
            'repeating-linear-gradient(-45deg, rgba(200,160,64,0.07) 0, rgba(200,160,64,0.07) 1px, transparent 1px, transparent 8px)',
          ].join(', '),
        }} />
      </div>
    );
  }

  // === FACE-UP ===
  const displayRank = rank !== undefined ? rankToDisplay(rank) : '';
  const displaySuit = suit ? suitToSymbol(suit) : '';

  // XS layout: rank top-left, suit bottom-right, no center suit
  if (isXS) {
    return (
      <div style={rootStyle} className={className}>
        {/* Top-left rank */}
        <div style={{
          position: 'absolute',
          top: spec.tlTop,
          left: spec.tlLeft,
          lineHeight: 1,
        }}>
          <span style={{
            fontSize: spec.rankFontSize,
            fontFamily: 'Georgia, serif',
            fontWeight: 900,
            color: suitColor,
            userSelect: 'none',
          }}>
            {displayRank}
          </span>
        </div>
        {/* Bottom-right suit */}
        <span style={{
          position: 'absolute',
          bottom: 4,
          right: 4,
          fontSize: spec.suitFontSize,
          lineHeight: 1,
          color: suitColor,
          userSelect: 'none',
        }}>
          {displaySuit}
        </span>
      </div>
    );
  }

  // LG / MD / SM layout: rank top-left, large suit center, no bottom-right
  return (
    <div style={rootStyle} className={className}>
      {/* Top-left: rank only */}
      <div style={{
        position: 'absolute',
        top: spec.tlTop,
        left: spec.tlLeft,
        lineHeight: 1,
      }}>
        <span style={{
          fontSize: spec.rankFontSize,
          fontFamily: 'Georgia, serif',
          fontWeight: 900,
          color: suitColor,
          userSelect: 'none',
        }}>
          {displayRank}
        </span>
      </div>

      {/* Center large suit */}
      <div style={{
        position: 'absolute',
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
        lineHeight: 1,
      }}>
        <span style={{
          fontSize: spec.suitFontSize,
          color: suitColor,
          userSelect: 'none',
        }}>
          {displaySuit}
        </span>
      </div>
    </div>
  );
};

export default Card;

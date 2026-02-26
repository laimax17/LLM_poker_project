import React from 'react';

interface BotSpeechBubbleProps {
  text: string;
  side: 'right' | 'left';
  fading?: boolean;
}

/**
 * Floating AI speech bubble anchored to PlayerBox's main card (position:relative).
 * side="right" → bubble extends rightward (for left-column bots)
 * side="left"  → bubble extends leftward  (for right-column bots)
 * fading=true  → plays fadeOutSlide exit animation before DOM removal
 */
const BotSpeechBubble: React.FC<BotSpeechBubbleProps> = ({ text, side, fading }) => {
  const isRight = side === 'right';
  const animation = fading
    ? 'fadeOutSlide 0.5s ease-in forwards'
    : `${isRight ? 'fadeInSlide' : 'fadeInSlideLeft'} 0.2s ease-out`;

  return (
    <div style={{
      position: 'absolute',
      ...(isRight
        ? { left: 'calc(100% + 8px)', top: 0 }
        : { right: 'calc(100% + 8px)', top: 0 }),
      width: 200,
      background: 'rgba(8, 7, 0, 0.96)',
      border: '1px solid var(--gold-d)',
      boxShadow: '0 0 8px rgba(200,160,64,0.15)',
      clipPath: 'var(--clip-sm)',
      padding: '8px 12px',
      fontFamily: 'var(--font-ai)',
      fontSize: 20,
      color: '#c8b080',
      lineHeight: 1.3,
      zIndex: 5,
      pointerEvents: 'none',
      animation,
      overflow: 'hidden',
      wordBreak: 'break-word',
    }}>
      {text}
    </div>
  );
};

export default BotSpeechBubble;

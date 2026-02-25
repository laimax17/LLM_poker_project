import React from 'react';

interface BotSpeechBubbleProps {
  text: string;
  side: 'right' | 'left';
}

/**
 * Floating AI speech bubble anchored to PlayerBox's main card (position:relative).
 * side="right" → bubble extends rightward (for left-column bots)
 * side="left"  → bubble extends leftward  (for right-column bots)
 */
const BotSpeechBubble: React.FC<BotSpeechBubbleProps> = ({ text, side }) => {
  const isRight = side === 'right';

  return (
    <div style={{
      position: 'absolute',
      ...(isRight
        ? { left: 'calc(100% + 8px)', top: 0 }
        : { right: 'calc(100% + 8px)', top: 0 }),
      width: 160,
      background: 'rgba(8, 7, 0, 0.96)',
      border: '1px solid var(--gold-d)',
      boxShadow: '0 0 8px rgba(200,160,64,0.15)',
      clipPath: 'var(--clip-sm)',
      padding: '6px 10px',
      fontFamily: 'var(--font-ai)',
      fontSize: 18,
      color: '#c8b080',
      lineHeight: 1.3,
      zIndex: 5,
      pointerEvents: 'none',
      animation: `${isRight ? 'fadeInSlide' : 'fadeInSlideLeft'} 0.2s ease-out`,
      overflow: 'hidden',
      wordBreak: 'break-word',
    }}>
      {text}
    </div>
  );
};

export default BotSpeechBubble;

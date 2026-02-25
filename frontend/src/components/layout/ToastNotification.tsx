import React from 'react';

interface ToastNotificationProps {
  message: string;
}

/**
 * Fixed-position error toast shown at the bottom center of the screen.
 * Auto-dismissed by the store after 3 seconds.
 */
const ToastNotification: React.FC<ToastNotificationProps> = ({ message }) => {
  return (
    <div style={{
      position: 'fixed',
      bottom: 80,
      left: '50%',
      transform: 'translateX(-50%)',
      background: '#1a0000',
      border: '2px solid var(--red)',
      color: '#ff8888',
      fontFamily: 'var(--font-label)',
      fontSize: 6,
      padding: '10px 20px',
      clipPath: 'var(--clip-xs)',
      animation: 'fadeInSlide 0.2s ease-out',
      zIndex: 999,
      whiteSpace: 'nowrap',
      pointerEvents: 'none',
    }}>
      ⚠ {message}
    </div>
  );
};

export default ToastNotification;

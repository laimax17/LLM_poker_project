import React from 'react';
import type { TournamentState } from '../../types';
import { useT } from '../../i18n/I18nContext';

interface TournamentHUDProps {
  tournament: TournamentState;
}

const cell = (label: string, value: React.ReactNode, color?: string) => (
  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', minWidth: 56 }}>
    <span
      style={{
        fontSize: 6,
        color: 'var(--gold-d)',
        letterSpacing: 1,
        fontFamily: 'var(--font-label)',
        marginBottom: 3,
      }}
    >
      {label}
    </span>
    <span style={{ fontFamily: 'var(--font-ui)', fontSize: 12, color: color ?? 'var(--gold)' }}>
      {value}
    </span>
  </div>
);

const TournamentHUD: React.FC<TournamentHUDProps> = ({ tournament }) => {
  const { t } = useT();
  const placeColor =
    tournament.yourPlace === 1 ? '#ffcc00' : tournament.playersRemaining <= 2 ? '#88ddaa' : 'var(--gold)';

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 18,
        padding: '6px 14px',
        background: 'var(--surface)',
        border: '2px solid var(--brown)',
        clipPath: 'var(--clip-sm)',
        flexWrap: 'wrap',
      }}
    >
      {cell(t('tour.level'), tournament.level)}
      {cell(t('tour.blinds'), `${tournament.smallBlind}/${tournament.bigBlind}`)}
      {tournament.ante > 0 && cell(t('tour.ante'), tournament.ante)}
      {cell(
        t('tour.nextLevel'),
        tournament.handsUntilNextLevel > 0 ? `${tournament.handsUntilNextLevel}h` : 'MAX',
      )}
      {cell(
        t('tour.remaining'),
        `${tournament.playersRemaining}/${tournament.totalPlayers}`,
      )}
      {cell(t('tour.place'), `#${tournament.yourPlace}`, placeColor)}
    </div>
  );
};

export default TournamentHUD;

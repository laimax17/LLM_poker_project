import React from 'react';
import type { GameState } from '../../types';
import PlayerBox from '../player/PlayerBox';
import HumanPanel from '../player/HumanPanel';
import PotDisplay from './PotDisplay';
import CommunityCards from './CommunityCards';
import HoleCards from './HoleCards';
import { useT } from '../../i18n/I18nContext';
import { useIsMobile } from '../../hooks/useIsMobile';

interface PokerTableProps {
  gameState: GameState;
  handCount: number;
}

const STREET_LABEL: Record<string, string> = {
  PREFLOP: 'PRE-FLOP',
  FLOP: 'FLOP',
  TURN: 'TURN',
  RIVER: 'RIVER',
  SHOWDOWN: 'SHOWDOWN',
  FINISHED: 'SHOWDOWN',
};

function getBadge(playerIdx: number, dealerIdx: number, total: number): string | undefined {
  const sb = (dealerIdx + 1) % total;
  const bb = (dealerIdx + 2) % total;
  if (playerIdx === dealerIdx) return 'BTN';
  if (playerIdx === sb) return 'SB';
  if (playerIdx === bb) return 'BB';
  return undefined;
}

const PokerTable: React.FC<PokerTableProps> = ({ gameState, handCount }) => {
  const { t } = useT();
  const isMobile = useIsMobile();
  const { players, community_cards, pot, state, current_player_idx, winning_cards, winners } = gameState;

  const isShowdown = (state === 'SHOWDOWN' || state === 'FINISHED') && winning_cards.length > 0;
  const humanPlayer = players[0];
  const botPlayers = players.slice(1);
  const dealerIdx = Math.max(0, players.findIndex((p) => p.is_dealer));
  const total = players.length;

  const isActiveHumanTurn =
    current_player_idx === 0 && state !== 'SHOWDOWN' && state !== 'FINISHED';

  const winnerNames =
    state === 'SHOWDOWN' || state === 'FINISHED'
      ? winners.map((id) => players.find((p) => p.id === id)?.name ?? id).join(' & ')
      : '';

  return (
    <div
      style={{
        flex: 1,
        minHeight: 0,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        padding: '8px 12px 0',
        gap: 6,
      }}
    >
      {/* Opponents row */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'flex-start',
          gap: isMobile ? 6 : 14,
          flexWrap: 'wrap',
          width: '100%',
          flexShrink: 0,
        }}
      >
        {botPlayers.map((bot, i) => (
          <PlayerBox
            key={bot.id}
            player={bot}
            isCurrentTurn={current_player_idx === i + 1}
            badge={getBadge(i + 1, dealerIdx, total)}
            winningCards={isShowdown && winners.includes(bot.id) ? winning_cards : undefined}
            compact={isMobile}
          />
        ))}
      </div>

      {/* Felt */}
      <div
        style={{
          flex: 1,
          minHeight: 150,
          width: '100%',
          maxWidth: 760,
          borderRadius: 120,
          background: 'radial-gradient(ellipse at 50% 45%, var(--felt) 0%, var(--felt-edge) 82%)',
          border: '8px solid var(--rail)',
          boxShadow: 'inset 0 0 60px rgba(0,0,0,0.5), 0 12px 30px rgba(0,0,0,0.5)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 14,
          position: 'relative',
          padding: 16,
        }}
      >
        {/* Street label */}
        <div
          style={{
            position: 'absolute',
            top: 14,
            fontSize: 11,
            fontWeight: 800,
            letterSpacing: 4,
            color: 'rgba(255,255,255,0.4)',
          }}
        >
          {STREET_LABEL[state] ?? state}
        </div>

        <PotDisplay pot={pot} />
        <CommunityCards cards={community_cards} winningCards={isShowdown ? winning_cards : undefined} />

        {/* Winner banner */}
        {(state === 'SHOWDOWN' || state === 'FINISHED') && winners.length > 0 && (
          <div
            key={winners.join('-')}
            style={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              background: 'rgba(0,0,0,0.9)',
              border: '3px solid var(--gold)',
              borderRadius: 16,
              padding: '14px 28px',
              textAlign: 'center',
              whiteSpace: 'nowrap',
              zIndex: 10,
              animation: 'popIn 0.4s cubic-bezier(0.34,1.56,0.64,1) both',
            }}
          >
            <div style={{ fontSize: 11, color: 'var(--gold-d)', letterSpacing: 2, marginBottom: 6, fontWeight: 700 }}>
              {t('showdown.label')}
            </div>
            <div style={{ fontFamily: 'var(--font-ui)', fontSize: 20, color: 'var(--gold-l)', marginBottom: 4 }}>
              {winnerNames}
            </div>
            <div style={{ fontSize: 13, color: 'var(--text)', fontWeight: 600 }}>{gameState.winning_hand}</div>
          </div>
        )}
      </div>

      {/* Hero */}
      <div style={{ flexShrink: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6, paddingBottom: 6 }}>
        {humanPlayer && (
          <HoleCards
            cards={humanPlayer.hand}
            handCount={handCount}
            isHumanTurn={isActiveHumanTurn}
            winningCards={isShowdown && winners.includes(humanPlayer.id) ? winning_cards : undefined}
          />
        )}
        {humanPlayer && (
          <HumanPanel
            player={humanPlayer}
            dealerIdx={dealerIdx}
            playerIdx={0}
            totalPlayers={total}
            isHumanTurn={isActiveHumanTurn}
          />
        )}
      </div>
    </div>
  );
};

export default PokerTable;

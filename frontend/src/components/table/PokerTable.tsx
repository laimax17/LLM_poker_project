import React from 'react';
import type { GameState } from '../../types';
import PlayerBox from '../player/PlayerBox';
import HumanPanel from '../player/HumanPanel';
import PotDisplay from './PotDisplay';
import CommunityCards from './CommunityCards';
import HoleCards from './HoleCards';

interface PokerTableProps {
  gameState: GameState;
}

/**
 * Derive position badge for a player.
 * players[0] is always human; bots are 1-5.
 * dealerIdx is augmented into the state by main.py broadcast_state().
 */
function getBadge(
  playerIdx: number,
  dealerIdx: number,
  totalPlayers: number,
): string | undefined {
  const sbIdx = (dealerIdx + 1) % totalPlayers;
  const bbIdx = (dealerIdx + 2) % totalPlayers;
  if (playerIdx === dealerIdx) return 'BTN';
  if (playerIdx === sbIdx) return 'SB';
  if (playerIdx === bbIdx) return 'BB';
  return undefined;
}

const PokerTable: React.FC<PokerTableProps> = ({ gameState }) => {
  const { players, community_cards, pot, state, current_player_idx } = gameState;

  // players[0] = human; bots = players[1..5]
  const humanPlayer = players[0];
  const botPlayers = players.slice(1); // indices 1-5

  // Determine dealer index (server augments is_dealer into each player)
  const dealerIdx = players.findIndex(p => p.is_dealer);
  const effectiveDealerIdx = dealerIdx >= 0 ? dealerIdx : 0;
  const totalPlayers = players.length;

  // Left column: bots at indices 1, 2, 3 → botPlayers[0,1,2]
  const leftBots = botPlayers.slice(0, 3);
  // Right column: bots at indices 4, 5 → botPlayers[3,4]
  const rightBots = botPlayers.slice(3, 5);

  return (
    <div style={{
      width: '100%',
      maxWidth: 1100,
      padding: '12px 8px',
      display: 'grid',
      gridTemplateColumns: '190px 1fr 190px',
      gridTemplateRows: 'auto',
    }}>
      {/* Felt wrap — spans all 3 columns */}
      <div style={{
        gridColumn: '1 / 4',
        gridRow: '1 / 3',
        position: 'relative',
      }}>
        {/* The green felt */}
        <div style={{
          width: '100%',
          minHeight: 560,
          background: 'radial-gradient(ellipse 80% 70% at 50% 42%, var(--felt-c) 0%, #122012 55%, var(--felt-e) 100%)',
          border: '5px solid var(--gold)',
          boxShadow: '0 0 0 2px var(--gold-d), inset 0 0 60px rgba(0,0,0,0.45), 0 0 40px rgba(200,160,64,0.06)',
          position: 'relative',
          overflow: 'hidden',
        }}>
          {/* Top-left corner L */}
          <div style={{
            position: 'absolute', top: 6, left: 6,
            width: 18, height: 18,
            borderTop: '3px solid var(--gold)',
            borderLeft: '3px solid var(--gold)',
            pointerEvents: 'none',
          }} />
          {/* Top-right corner L */}
          <div style={{
            position: 'absolute', top: 6, right: 6,
            width: 18, height: 18,
            borderTop: '3px solid var(--gold)',
            borderRight: '3px solid var(--gold)',
            pointerEvents: 'none',
          }} />

          {/* Left bots (3) */}
          <div style={{
            position: 'absolute',
            left: 10,
            top: 20,
            display: 'flex',
            flexDirection: 'column',
            gap: 12,
          }}>
            {leftBots.map((bot, i) => {
              const playerIdx = i + 1; // bot 0→idx1, bot 1→idx2, bot 2→idx3
              return (
                <PlayerBox
                  key={bot.id}
                  player={bot}
                  isCurrentTurn={current_player_idx === playerIdx}
                  chipBubbleSide="right"
                  badge={getBadge(playerIdx, effectiveDealerIdx, totalPlayers)}
                />
              );
            })}
          </div>

          {/* Right bots (2) */}
          <div style={{
            position: 'absolute',
            right: 10,
            top: 20,
            display: 'flex',
            flexDirection: 'column',
            gap: 12,
            alignItems: 'flex-end',
          }}>
            {rightBots.map((bot, i) => {
              const playerIdx = i + 4; // bot 3→idx4, bot 4→idx5
              return (
                <PlayerBox
                  key={bot.id}
                  player={bot}
                  isCurrentTurn={current_player_idx === playerIdx}
                  chipBubbleSide="left"
                  badge={getBadge(playerIdx, effectiveDealerIdx, totalPlayers)}
                />
              );
            })}
          </div>

          {/* Table center: pot + community cards */}
          <div style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -55%)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 12,
          }}>
            <PotDisplay pot={pot} street={state} />
            <CommunityCards cards={community_cards} />
          </div>

          {/* Human hole cards (bottom center) */}
          {humanPlayer && (
            <HoleCards
              cards={humanPlayer.hand}
              isHumanTurn={
                current_player_idx === 0 &&
                state !== 'SHOWDOWN' &&
                state !== 'FINISHED'
              }
            />
          )}

          {/* Human player info box (bottom right) */}
          {humanPlayer && (
            <div style={{
              position: 'absolute',
              bottom: 20,
              right: 10,
            }}>
              <HumanPanel
                player={humanPlayer}
                dealerIdx={effectiveDealerIdx}
                playerIdx={0}
                totalPlayers={totalPlayers}
                isHumanTurn={
                  current_player_idx === 0 &&
                  state !== 'SHOWDOWN' &&
                  state !== 'FINISHED'
                }
              />
            </div>
          )}

          {/* Winner announcement */}
          {(state === 'SHOWDOWN' || state === 'FINISHED') && gameState.winners.length > 0 && (() => {
            const winnerNames = gameState.winners
              .map(id => players.find(p => p.id === id)?.name ?? id)
              .join(' & ');
            return (
              <div style={{
                position: 'absolute',
                top: '30%',
                left: '50%',
                transform: 'translateX(-50%)',
                background: 'rgba(0,0,0,0.88)',
                border: '3px solid var(--gold)',
                padding: '14px 28px',
                textAlign: 'center',
                clipPath: 'var(--clip-md)',
                zIndex: 10,
                whiteSpace: 'nowrap',
              }}>
                <div style={{ fontSize: 7, color: 'var(--gold-d)', letterSpacing: 3, marginBottom: 8, fontFamily: 'var(--font-label)' }}>
                  ◈ SHOWDOWN ◈
                </div>
                <div style={{ fontSize: 12, color: 'var(--gold)', letterSpacing: 1, marginBottom: 6, fontFamily: 'var(--font-ui)' }}>
                  {winnerNames}
                </div>
                <div style={{ fontSize: 8, color: 'var(--gold-l)', fontFamily: 'var(--font-label)', letterSpacing: 1 }}>
                  {gameState.winning_hand}
                </div>
              </div>
            );
          })()}
        </div>
      </div>
    </div>
  );
};

export default PokerTable;

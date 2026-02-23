import { useEffect } from 'react';
import { useGameStore } from './store/useGameStore';
import PokerTable from './components/table/PokerTable';
import ActionBar from './components/layout/ActionBar';
import LLMConfigBar from './components/layout/LLMConfigBar';
import AICoachPanel from './components/ai-coach/AICoachPanel';

function App() {
  const {
    connect,
    isConnected,
    gameState,
    startGame,
    sendAction,
    startNextHand,
    requestAdvice,
    closeCoach,
    coachAdvice,
    isRequestingAdvice,
    showCoach,
    llmConfig,
    setLLMConfig,
  } = useGameStore();

  useEffect(() => {
    connect();
  }, []);

  const isHumanTurn =
    gameState !== null &&
    gameState.state !== 'SHOWDOWN' &&
    gameState.state !== 'FINISHED' &&
    gameState.current_player_idx === 0;

  const isGameOver =
    gameState?.state === 'SHOWDOWN' || gameState?.state === 'FINISHED';

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      background: 'var(--bg)',
      overflow: 'hidden',
    }}>
      {/* ─── Header ─── */}
      <header style={{
        width: '100%',
        background: 'var(--surface)',
        borderBottom: '4px solid var(--gold)',
        padding: '14px 28px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexShrink: 0,
      }}>
        <div style={{
          fontFamily: 'var(--font-ui)',
          fontSize: 18,
          color: 'var(--gold)',
          textShadow: '2px 2px 0 var(--gold-d)',
          letterSpacing: 3,
        }}>
          CYBER <span style={{ color: 'var(--gold-l)' }}>HOLD'EM</span>
        </div>

        <div style={{
          fontSize: 6,
          color: 'var(--gold)',
          display: 'flex',
          gap: 20,
          fontFamily: 'var(--font-label)',
        }}>
          {gameState ? (
            <>
              <span>BLIND <b style={{ color: 'var(--gold-l)' }}>$10/$20</b></span>
              <span>STREET <b style={{ color: 'var(--gold-l)' }}>{gameState.state}</b></span>
              <span>POT <b style={{ color: 'var(--gold-l)' }}>${gameState.pot}</b></span>
            </>
          ) : (
            <span style={{ color: isConnected ? '#44cc66' : '#cc4444' }}>
              {isConnected ? '● CONNECTED' : '● DISCONNECTED'}
            </span>
          )}
        </div>
      </header>

      {/* ─── Main Content ─── */}
      <main style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        width: '100%',
        overflowY: 'auto',
      }}>
        {!gameState ? (
          /* Start Screen */
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            flex: 1,
            gap: 24,
            padding: 40,
          }}>
            <div style={{
              fontFamily: 'var(--font-ui)',
              fontSize: 28,
              color: 'var(--gold)',
              textShadow: '0 0 20px rgba(200,160,64,0.5)',
              letterSpacing: 4,
              textAlign: 'center',
            }}>
              CYBER HOLD'EM
            </div>
            <div style={{
              fontSize: 7,
              color: 'var(--gold-d)',
              letterSpacing: 2,
              fontFamily: 'var(--font-label)',
            }}>
              1 HUMAN VS 5 AI BOTS
            </div>
            <button
              className="abtn abtn-raise"
              style={{ fontSize: 10, padding: '14px 28px', marginTop: 16 }}
              onClick={() => startGame()}
            >
              ▶ START GAME
            </button>
          </div>
        ) : (
          <>
            {/* Poker table */}
            <PokerTable gameState={gameState} />

            {/* Action bar */}
            <ActionBar
              gameState={gameState}
              onAction={sendAction}
              onAskAI={requestAdvice}
              isRequestingAdvice={isRequestingAdvice}
              disabled={!isHumanTurn}
            />

            {/* Next hand button */}
            {isGameOver && (
              <div style={{ padding: '8px 0 4px' }}>
                <button
                  className="abtn abtn-raise"
                  onClick={startNextHand}
                >
                  ▶ NEXT HAND
                </button>
              </div>
            )}

            {/* LLM config bar */}
            <LLMConfigBar
              config={llmConfig}
              onConfigChange={setLLMConfig}
            />
          </>
        )}
      </main>

      {/* ─── AI Coach Modal (always rendered at root level) ─── */}
      {showCoach && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.65)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: 24,
          }}
          onClick={(e) => {
            if (e.target === e.currentTarget && !isRequestingAdvice) closeCoach();
          }}
        >
          <AICoachPanel
            advice={coachAdvice}
            isLoading={isRequestingAdvice}
            onClose={closeCoach}
          />
        </div>
      )}
    </div>
  );
}

export default App;

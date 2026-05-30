import { useEffect, useState } from 'react';
import { useGameStore } from './store/useGameStore';
import { useT } from './i18n/I18nContext';
import PokerTable from './components/table/PokerTable';
import ActionBar from './components/layout/ActionBar';
import LLMConfigBar from './components/layout/LLMConfigBar';
import AICoachPanel from './components/ai-coach/AICoachPanel';
import ToastNotification from './components/layout/ToastNotification';
import LiveHintBar from './components/learning/LiveHintBar';
import HandReviewModal from './components/learning/HandReviewModal';
import SessionStatsPanel from './components/learning/SessionStatsPanel';
import SetupLobby from './components/lobby/SetupLobby';
import TournamentHUD from './components/table/TournamentHUD';
import StandingsModal from './components/table/StandingsModal';
import AllInEquityOverlay from './components/table/AllInEquityOverlay';

function App() {
  const { t, locale, setLocale } = useT();
  const {
    connect,
    isConnected,
    gameState,
    startGame,
    sendAction,
    startNextHand,
    resetGame,
    requestAdvice,
    closeCoach,
    coachAdvice,
    isRequestingAdvice,
    showCoach,
    llmConfig,
    setLLMConfig,
    setLocale: setBackendLocale,
    errorMessage,
    handCount,
    actionInFlight,
    isGameOver: isPlayerEliminated,
    learningMode,
    setLearningMode,
    liveHint,
    handReview,
    showReview,
    closeReview,
    sessionStats,
    showStats,
    toggleStats,
    tournament,
    standings,
    closeStandings,
    lastElimination,
    levelUpFlash,
    allinEquity,
  } = useGameStore();

  const [showMenu, setShowMenu] = useState(false);
  // Delay "Next Hand" button by 2.5s after hand ends so player can see the result
  const [showNextHandBtn, setShowNextHandBtn] = useState(false);

  useEffect(() => {
    connect();
    return () => {
      useGameStore.getState().socket?.disconnect();
    };
  }, []);

  // Sync locale to backend whenever it changes
  useEffect(() => {
    setBackendLocale(locale);
  }, [locale, setBackendLocale]);

  // Show "Next Hand" button 2.5s after hand ends so player can read the result
  const isHandOver = gameState?.state === 'SHOWDOWN' || gameState?.state === 'FINISHED';
  useEffect(() => {
    if (!isHandOver) {
      setShowNextHandBtn(false);
      return;
    }
    const timer = setTimeout(() => setShowNextHandBtn(true), 2500);
    return () => clearTimeout(timer);
  }, [isHandOver]);

  const isHumanTurn =
    gameState !== null &&
    gameState.state !== 'SHOWDOWN' &&
    gameState.state !== 'FINISHED' &&
    gameState.current_player_idx === 0;

  const handleLanguageChange = (newLocale: 'en' | 'zh') => {
    setLocale(newLocale);
  };

  const handleNewGame = () => {
    setShowMenu(false);
    resetGame();
    startGame();
  };

  return (
    <div style={{
      height: '100vh',
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
        padding: '10px 20px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexShrink: 0,
      }}>
        <div style={{
          fontFamily: 'var(--font-ui)',
          fontSize: 20,
          color: 'var(--gold)',
          textShadow: '2px 2px 0 var(--gold-d)',
          letterSpacing: 3,
          display: 'flex',
          alignItems: 'center',
          gap: 16,
        }}>
          {t('app.title')}

          {/* Menu button — visible during gameplay */}
          {gameState && (
            <button
              onClick={() => setShowMenu(true)}
              style={{
                background: 'none',
                border: '1px solid var(--gold-d)',
                color: 'var(--gold-d)',
                fontSize: 7,
                padding: '4px 10px',
                cursor: 'pointer',
                fontFamily: 'var(--font-label)',
                letterSpacing: 1,
              }}
            >
              {t('app.menu')}
            </button>
          )}
        </div>

        <div style={{
          fontSize: 8,
          color: 'var(--gold)',
          display: 'flex',
          gap: 20,
          fontFamily: 'var(--font-label)',
        }}>
          {gameState ? (
            <>
              <span>{t('header.blind')} <b style={{ color: 'var(--gold-l)' }}>$10/$20</b></span>
              <span>{t('header.street')} <b style={{ color: 'var(--gold-l)' }}>{gameState.state}</b></span>
              <span>{t('header.pot')} <b style={{ color: 'var(--gold-l)' }}>${gameState.pot}</b></span>
              <span>{t('header.hand')} <b style={{ color: 'var(--gold-l)' }}>#{String(handCount).padStart(3, '0')}</b></span>
            </>
          ) : (
            <span style={{ color: isConnected ? '#44cc66' : '#cc4444' }}>
              {isConnected ? t('header.connected') : t('header.disconnected')}
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
        overflow: 'hidden',
        minHeight: 0,
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
              fontSize: 32,
              color: 'var(--gold)',
              textShadow: '0 0 20px rgba(200,160,64,0.5)',
              letterSpacing: 4,
              textAlign: 'center',
            }}>
              {t('app.title')}
            </div>
            <div style={{
              fontSize: 10,
              color: 'var(--gold-d)',
              letterSpacing: 2,
              fontFamily: 'var(--font-label)',
            }}>
              {t('app.subtitle')}
            </div>

            {/* Language selector */}
            <div style={{ display: 'flex', gap: 12, marginTop: 8 }}>
              <button
                onClick={() => handleLanguageChange('en')}
                style={{
                  background: locale === 'en' ? 'var(--gold)' : 'transparent',
                  border: '2px solid var(--gold)',
                  color: locale === 'en' ? '#000' : 'var(--gold)',
                  fontSize: 9,
                  padding: '8px 16px',
                  cursor: 'pointer',
                  fontFamily: 'var(--font-label)',
                  letterSpacing: 1,
                }}
              >
                ENGLISH
              </button>
              <button
                onClick={() => handleLanguageChange('zh')}
                style={{
                  background: locale === 'zh' ? 'var(--gold)' : 'transparent',
                  border: '2px solid var(--gold)',
                  color: locale === 'zh' ? '#000' : 'var(--gold)',
                  fontSize: 9,
                  padding: '8px 16px',
                  cursor: 'pointer',
                  fontFamily: 'var(--font-label)',
                  letterSpacing: 1,
                }}
              >
                中文
              </button>
            </div>

            <SetupLobby onStart={(cfg) => startGame(cfg)} />
          </div>
        ) : (
          <>
            {/* Tournament HUD */}
            {tournament?.active && (
              <div style={{ display: 'flex', justifyContent: 'center', padding: '4px 8px 8px' }}>
                <TournamentHUD tournament={tournament} />
              </div>
            )}

            {/* Poker table */}
            <div style={{ flex: 1, minHeight: 0, width: '100%', display: 'flex', flexDirection: 'column' }}>
              <PokerTable gameState={gameState} handCount={handCount} />
            </div>

            {/* Live GTO hint — Learning Mode only, while it's the human's turn */}
            {learningMode && liveHint && isHumanTurn && (
              <LiveHintBar hint={liveHint} />
            )}

            {/* Action bar */}
            <ActionBar
              gameState={gameState}
              onAction={sendAction}
              onAskAI={requestAdvice}
              isRequestingAdvice={isRequestingAdvice}
              disabled={!isHumanTurn || actionInFlight}
              showCoach={showCoach}
            />

            {/* Next hand button — always rendered, visibility toggled to prevent layout shift */}
            <div style={{
              padding: '10px 0 6px',
              display: 'flex',
              justifyContent: 'center',
              visibility: showNextHandBtn ? 'visible' : 'hidden',
              flexShrink: 0,
            }}>
              <button
                className="abtn abtn-raise"
                onClick={startNextHand}
              >
                {t('app.nextHand')}
              </button>
            </div>

            {/* LLM config bar */}
            <LLMConfigBar
              config={llmConfig}
              onConfigChange={setLLMConfig}
              learningMode={learningMode}
              onLearningModeChange={setLearningMode}
              onToggleStats={toggleStats}
            />
          </>
        )}
      </main>

      {/* ─── Learning Mode: post-hand review + session stats ─── */}
      {showReview && handReview && (
        <HandReviewModal review={handReview} onClose={closeReview} />
      )}
      {showStats && sessionStats && (
        <SessionStatsPanel stats={sessionStats} onClose={toggleStats} />
      )}

      {/* ─── Tournament: final standings ─── */}
      {standings && (
        <StandingsModal
          standings={standings}
          onPlayAgain={() => { closeStandings(); resetGame(); }}
        />
      )}

      {/* ─── All-in equity overlay ─── */}
      {allinEquity && <AllInEquityOverlay data={allinEquity} />}

      {/* ─── Tournament: blind level-up flash ─── */}
      {levelUpFlash && (
        <div style={{
          position: 'fixed', top: '18%', left: '50%', transform: 'translateX(-50%)',
          zIndex: 1700, pointerEvents: 'none', textAlign: 'center',
          background: 'rgba(0,0,0,0.7)', border: '2px solid var(--gold)',
          padding: '10px 22px', clipPath: 'var(--clip-sm)',
          animation: 'fadeInSlide 0.3s ease-out',
        }}>
          <div style={{ fontFamily: 'var(--font-ui)', fontSize: 14, color: '#ffcc00',
            textShadow: '0 0 10px rgba(255,204,0,0.6)', letterSpacing: 2 }}>
            {t('tour.blindsUp')} L{levelUpFlash.level}
          </div>
          <div style={{ fontFamily: 'var(--font-label)', fontSize: 9, color: 'var(--gold-d)', marginTop: 4 }}>
            {levelUpFlash.smallBlind}/{levelUpFlash.bigBlind}
          </div>
        </div>
      )}

      {/* ─── Tournament: elimination toast ─── */}
      {lastElimination && (
        <div style={{
          position: 'fixed', bottom: '16%', left: '50%', transform: 'translateX(-50%)',
          zIndex: 1700, pointerEvents: 'none',
          background: 'rgba(0,0,0,0.78)', border: '2px solid #cc6666',
          padding: '8px 18px', clipPath: 'var(--clip-sm)',
          animation: 'fadeInSlide 0.3s ease-out',
        }}>
          <span style={{ fontFamily: 'var(--font-label)', fontSize: 9, color: '#ff8888', letterSpacing: 1 }}>
            ☠ {lastElimination.id === 'human' ? t('human.you') : lastElimination.name} — #{lastElimination.place}
          </span>
        </div>
      )}

      {/* ─── Disconnect overlay — covers table when socket lost during gameplay ─── */}
      {gameState && !isConnected && (
        <div style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(0,0,0,0.75)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1800,
          gap: 14,
          pointerEvents: 'none',
        }}>
          <div style={{
            fontFamily: 'var(--font-ui)',
            fontSize: 20,
            color: '#cc4444',
            letterSpacing: 4,
            animation: 'blink 1s steps(1) infinite',
          }}>
            DISCONNECTED
          </div>
          <div style={{
            fontFamily: 'var(--font-label)',
            fontSize: 8,
            color: 'var(--gold-d)',
            letterSpacing: 2,
          }}>
            RECONNECTING...
          </div>
        </div>
      )}

      {/* ─── Error Toast ─── */}
      {errorMessage && <ToastNotification message={errorMessage} />}

      {/* ─── Game Over Overlay ─── */}
      {isPlayerEliminated && (
        <div style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(0,0,0,0.85)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 2000,
          gap: 20,
        }}>
          <div style={{
            fontFamily: 'var(--font-ui)',
            fontSize: 28,
            color: '#ff4444',
            letterSpacing: 4,
            textShadow: '0 0 20px rgba(255,68,68,0.5)',
          }}>
            {t('gameover.title')}
          </div>
          <div style={{
            fontFamily: 'var(--font-ai)',
            fontSize: 22,
            color: '#c8b080',
            textAlign: 'center',
          }}>
            {t('gameover.eliminated')}
          </div>
          <button
            className="abtn abtn-raise"
            style={{ fontSize: 13, padding: '16px 32px', marginTop: 16 }}
            onClick={handleNewGame}
          >
            {t('app.newGame')}
          </button>
        </div>
      )}

      {/* ─── Menu Overlay ─── */}
      {showMenu && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.75)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1500,
            gap: 16,
          }}
          onClick={(e) => {
            if (e.target === e.currentTarget) setShowMenu(false);
          }}
        >
          <div style={{
            background: 'var(--surface)',
            border: '4px solid var(--gold)',
            padding: '28px 36px',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 16,
            clipPath: 'var(--clip-md)',
          }}>
            <div style={{
              fontFamily: 'var(--font-ui)',
              fontSize: 14,
              color: 'var(--gold)',
              letterSpacing: 3,
              marginBottom: 8,
            }}>
              {t('app.menu')}
            </div>

            {/* Language selector in menu */}
            <div style={{ display: 'flex', gap: 12 }}>
              <button
                onClick={() => handleLanguageChange('en')}
                style={{
                  background: locale === 'en' ? 'var(--gold)' : 'transparent',
                  border: '2px solid var(--gold)',
                  color: locale === 'en' ? '#000' : 'var(--gold)',
                  fontSize: 8,
                  padding: '6px 14px',
                  cursor: 'pointer',
                  fontFamily: 'var(--font-label)',
                  letterSpacing: 1,
                }}
              >
                ENGLISH
              </button>
              <button
                onClick={() => handleLanguageChange('zh')}
                style={{
                  background: locale === 'zh' ? 'var(--gold)' : 'transparent',
                  border: '2px solid var(--gold)',
                  color: locale === 'zh' ? '#000' : 'var(--gold)',
                  fontSize: 8,
                  padding: '6px 14px',
                  cursor: 'pointer',
                  fontFamily: 'var(--font-label)',
                  letterSpacing: 1,
                }}
              >
                中文
              </button>
            </div>

            <button
              className="abtn abtn-raise"
              style={{ fontSize: 11, padding: '12px 28px' }}
              onClick={handleNewGame}
            >
              {t('app.newGame')}
            </button>
            <button
              className="abtn abtn-check"
              style={{ fontSize: 11, padding: '12px 28px' }}
              onClick={() => setShowMenu(false)}
            >
              {t('app.continue')}
            </button>
          </div>
        </div>
      )}

      {/* ─── Portrait Rotation Prompt (mobile only, CSS-driven) ─── */}
      <div className="portrait-overlay">
        <div style={{
          fontFamily: 'var(--font-ui)',
          fontSize: 20,
          color: 'var(--gold)',
          letterSpacing: 3,
          marginBottom: 16,
        }}>
          ↺
        </div>
        <div style={{
          fontFamily: 'var(--font-label)',
          fontSize: 8,
          color: 'var(--gold-d)',
          letterSpacing: 2,
          textAlign: 'center',
        }}>
          ROTATE TO LANDSCAPE
        </div>
      </div>

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

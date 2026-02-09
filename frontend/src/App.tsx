import { useEffect } from 'react';
import { useGameStore } from './store/useGameStore';
import { PokerTable } from './components/PokerTable';
import { Controls } from './components/Controls';
// StartScreen is defined inline below

function App() {
  const { connect, isConnected, gameState } = useGameStore();

  useEffect(() => {
    connect();
  }, []);

  return (
    <div className="min-h-screen bg-cyber-bg text-white font-sans overflow-hidden flex flex-col">
      <header className="p-4 border-b border-white/10 flex justify-between items-center bg-black/50 backdrop-blur">
        <h1 className="text-2xl font-orbitron font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyber-neonBlue to-cyber-neonPurple">
          CYBER HOLD'EM
        </h1>
        <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500 shadow-[0_0_10px_#00ff00]' : 'bg-red-500'}`}></div>
      </header>

      <main className="flex-1 relative flex flex-col items-center justify-center p-4">
        {!gameState ? (
          <StartScreen />
        ) : (
          <>
            <PokerTable />
            <Controls />
          </>
        )}
      </main>
    </div>
  );
}

const StartScreen = () => {
  const { startGame } = useGameStore();
  return (
    <div className="text-center">
      <h2 className="text-4xl font-bold mb-8">Ready to Play?</h2>
      <button
        onClick={() => startGame()}
        className="px-8 py-3 bg-cyber-neonBlue text-black font-bold text-lg rounded hover:shadow-[0_0_20px_#00f0ff] transition-all"
      >
        START GAME
      </button>
    </div>
  )
}

export default App;

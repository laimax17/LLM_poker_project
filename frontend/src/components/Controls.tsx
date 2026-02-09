import { useState } from 'react';
import { useGameStore } from '../store/useGameStore';

export const Controls: React.FC = () => {
    const { gameState, sendAction, copyPrompt } = useGameStore();
    const [raiseAmount, setRaiseAmount] = useState(0);

    if (!gameState) return null;

    const me = gameState.players.find(p => p.id === 'human');
    if (!me || !me.is_active || gameState.state === 'FINISHED' || gameState.state === 'SHOWDOWN') return null;

    const isMyTurn = gameState.players[gameState.current_player_idx].id === 'human';
    const toCall = gameState.current_bet - me.current_bet;
    const canCheck = toCall === 0;

    const handleRaise = () => {
        // Logic to calculate total raise? 
        // Backend expects TOTAL bet.
        // If I raise BY X... 
        // Usually UI has 'Raise To'.
        // Let's assume input is TOTAL.
        // Min raise is current_bet + min_raise.
        const minTotal = gameState.current_bet + gameState.min_raise;
        const amount = Math.max(minTotal, raiseAmount);
        console.log('👆 User clicked [Raise]:', amount);
        sendAction('raise', amount);
    };

    const handleCopyPrompt = async () => {
        const text = copyPrompt();
        await navigator.clipboard.writeText(text);
        alert("Prompt copied to clipboard!");
    };

    return (
        <div className="fixed bottom-0 w-full bg-cyber-panel/90 backdrop-blur border-t border-cyber-neonBlue p-4 flex flex-col items-center gap-4">
            {/* Status Bar */}
            <div className="flex justify-between w-full max-w-4xl px-4 text-xs text-gray-400 font-mono">
                <span>Blind: {gameState.min_raise / 2}/{gameState.min_raise}</span>
                <span>Min Raise: {gameState.min_raise}</span>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-4 items-center">
                {isMyTurn ? (
                    <>
                        <button
                            onClick={() => { console.log('👆 User clicked [Fold]'); sendAction('fold'); }}
                            className="px-6 py-2 bg-red-900/50 hover:bg-red-800 border border-red-500 rounded text-red-200 uppercase font-bold tracking-wider"
                        >
                            Fold
                        </button>

                        {canCheck ? (
                            <button
                                onClick={() => { console.log('👆 User clicked [Check]'); sendAction('check'); }}
                                className="px-6 py-2 bg-gray-700/50 hover:bg-gray-600 border border-gray-400 rounded text-white uppercase font-bold tracking-wider"
                            >
                                Check
                            </button>
                        ) : (
                            <button
                                onClick={() => { console.log('👆 User clicked [Call]', toCall); sendAction('call'); }}
                                className="px-6 py-2 bg-blue-900/50 hover:bg-blue-800 border border-blue-500 rounded text-blue-200 uppercase font-bold tracking-wider"
                            >
                                Call ${toCall}
                            </button>
                        )}

                        <div className="flex flex-col gap-1 items-center bg-black/30 p-2 rounded border border-gray-700">
                            <input
                                type="range"
                                min={gameState.current_bet + gameState.min_raise}
                                max={me.chips + me.current_bet}
                                step={gameState.min_raise}
                                value={raiseAmount || (gameState.current_bet + gameState.min_raise)}
                                onChange={(e) => setRaiseAmount(Number(e.target.value))}
                                className="w-32 accent-cyber-neonPurple"
                            />
                            <button
                                onClick={handleRaise}
                                className="px-6 py-1 bg-cyber-neonPurple/20 hover:bg-cyber-neonPurple/40 border border-cyber-neonPurple rounded text-cyber-neonPurple uppercase font-bold text-sm"
                            >
                                Raise To {raiseAmount || (gameState.current_bet + gameState.min_raise)}
                            </button>
                        </div>
                    </>
                ) : (
                    <div className="text-white animate-pulse">Waiting for opponent...</div>
                )}
            </div>

            {/* Utilities */}
            <button
                onClick={handleCopyPrompt}
                className="absolute right-4 bottom-4 text-xs text-cyber-neonBlue underline hover:text-white"
            >
                [AI Help: Copy Prompt]
            </button>
        </div>
    );
};

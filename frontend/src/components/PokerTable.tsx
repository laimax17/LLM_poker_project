import { useState } from 'react';
import { motion } from 'framer-motion';
import { useGameStore } from '../store/useGameStore';
import { PlayerSeat } from './PlayerSeat';
import type { Card } from '../types';

export const PokerTable: React.FC = () => {
    const { gameState } = useGameStore();
    const [showResult, setShowResult] = useState(true);

    if (!gameState) return <div className="text-white">Waiting for game...</div>;

    // Find my index (human)
    const myIndex = gameState.players.findIndex(p => p.id === 'human');

    // Rotate players so I am at index 0 (bottom)
    // If I am not found (observer?), just use original order or index 0.
    const rotation = myIndex >= 0 ? myIndex : 0;

    const rotatedPlayers = [
        ...gameState.players.slice(rotation),
        ...gameState.players.slice(0, rotation)
    ];

    // Positions for 6 players: Bottom, BottomLeft, TopLeft, Top, TopRight, BottomRight
    // Actually, let's map index 0..5 to styles.
    // 0: Bottom (Human)
    // 1: Bottom Left
    // 2: Top Left
    // 3: Top
    // 4: Top Right
    // 5: Bottom Right


    const getPositionStyle = (index: number) => {
        switch (index) {
            case 0: return { bottom: '0%', left: '50%', transform: 'translate(-50%, 0)' }; // Bottom Center
            case 1: return { bottom: '20%', left: '5%', transform: 'translate(0, 0)' }; // Bottom Left
            case 2: return { top: '20%', left: '5%', transform: 'translate(0, 0)' }; // Top Left
            case 3: return { top: '0%', left: '50%', transform: 'translate(-50%, 0)' }; // Top Center
            case 4: return { top: '20%', right: '5%', transform: 'translate(0, 0)' }; // Top Right
            case 5: return { bottom: '20%', right: '5%', transform: 'translate(0, 0)' }; // Bottom Right
            default: return {};
        }
    };

    const isShowdown = gameState.state === 'SHOWDOWN' || gameState.state === 'FINISHED';

    return (
        <div className="relative w-full h-[600px] flex items-center justify-center">
            {/* Table Felt */}
            <div className="absolute w-[80%] h-[60%] bg-[#151515] rounded-[100px] border-4 border-cyber-panel shadow-[0_0_50px_rgba(0,240,255,0.1)] flex items-center justify-center relative">

                {/* Pot */}
                <div className="absolute top-1/3 text-white font-mono text-sm bg-black/50 px-3 py-1 rounded-full border border-gray-700 z-10">
                    Pot: <span className="text-cyber-neonBlue">${gameState.pot}</span>
                </div>

                {/* Showdown Result Overlay */}
                {isShowdown && (
                    <>
                        {showResult ? (
                            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50 flex flex-col items-center gap-4 animate-in fade-in zoom-in duration-300">
                                <div className="bg-black/90 border-2 border-cyber-neonPurple p-6 rounded-xl text-center backdrop-blur-md shadow-[0_0_50px_rgba(188,19,254,0.3)] min-w-[300px]">
                                    <h2 className="text-3xl font-orbitron font-bold text-cyber-neonPurple mb-2 drop-shadow-[0_0_5px_rgba(188,19,254,0.8)]">Showdown!</h2>

                                    <div className="mb-4">
                                        <p className="text-gray-400 text-sm uppercase tracking-widest mb-1">Winner</p>
                                        <p className="text-xl font-bold text-yellow-400">{gameState.winners.join(', ')}</p>
                                    </div>

                                    <div className="bg-cyber-neonPurple/10 rounded-lg p-3 mb-6 border border-cyber-neonPurple/30">
                                        <p className="text-cyber-neonBlue font-mono font-bold">{gameState.winning_hand}</p>
                                    </div>

                                    <div className="flex flex-col gap-3 w-full">
                                        <button
                                            onClick={() => { useGameStore.getState().startNextHand(); setShowResult(true); }}
                                            className="w-full py-3 bg-cyber-neonBlue text-black font-bold rounded hover:bg-white transition-all shadow-[0_0_20px_rgba(0,240,255,0.4)] hover:shadow-[0_0_30px_rgba(0,240,255,0.6)] uppercase tracking-wider"
                                        >
                                            Start Next Hand
                                        </button>

                                        <button
                                            onClick={() => setShowResult(false)}
                                            className="w-full py-2 bg-transparent text-gray-400 hover:text-white border border-gray-600 hover:border-gray-400 rounded transition-colors text-sm"
                                        >
                                            👁️ View Board
                                        </button>
                                    </div>
                                </div>
                            </div>
                        ) : (
                            <div className="absolute top-4 right-4 z-50">
                                <button
                                    onClick={() => setShowResult(true)}
                                    className="px-4 py-2 bg-black/80 text-cyber-neonPurple border border-cyber-neonPurple rounded-full shadow-[0_0_15px_rgba(188,19,254,0.3)] hover:bg-cyber-neonPurple/20 transition-all font-bold flex items-center gap-2"
                                >
                                    <span>🏆</span> Show Results
                                </button>

                                <button
                                    onClick={() => { useGameStore.getState().startNextHand(); setShowResult(true); }}
                                    className="mt-2 px-4 py-2 bg-cyber-neonBlue/20 text-cyber-neonBlue border border-cyber-neonBlue rounded-full hover:bg-cyber-neonBlue/40 transition-all font-bold w-full"
                                >
                                    Next Hand
                                </button>
                            </div>
                        )}
                    </>
                )}

                {/* Community Cards */}
                <div className="flex gap-2 z-10">
                    {gameState.community_cards.map((c, i) => (
                        <motion.div
                            key={i}
                            initial={{ y: -20, opacity: 0 }}
                            animate={{ y: 0, opacity: 1 }}
                            transition={{ delay: i * 0.1 }}
                        >
                            <CardView card={c} />
                        </motion.div>
                    ))}
                </div>
            </div>

            {/* Seats */}
            {rotatedPlayers.map((p, i) => (
                <div key={p.id} className="absolute" style={getPositionStyle(i)}>
                    <PlayerSeat
                        player={p}
                        position={i === 0 ? 'bottom' : 'top'}
                        isWinner={gameState.winners.includes(p.id)}
                    />
                </div>
            ))}
        </div>
    );
};

const CardView = ({ card }: { card: Card }) => (
    <div className="w-12 h-16 bg-white rounded flex flex-col items-center justify-center shadow-lg border border-gray-300">
        <span className={`text-lg font-bold ${['Hearts', 'Diamonds'].includes(card.suit) ? 'text-red-500' : 'text-black'}`}>
            {getRankSymbol(card.rank)}
        </span>
        <span className={`text-xs ${['Hearts', 'Diamonds'].includes(card.suit) ? 'text-red-500' : 'text-black'}`}>
            {getSuitSymbol(card.suit)}
        </span>
    </div>
)

function getRankSymbol(r: number): string {
    if (r <= 10) return r.toString();
    if (r === 11) return 'J';
    if (r === 12) return 'Q';
    if (r === 13) return 'K';
    if (r === 14) return 'A';
    return '?';
}

function getSuitSymbol(s: string): string {
    switch (s) {
        case 'Hearts': return '♥';
        case 'Diamonds': return '♦';
        case 'Clubs': return '♣';
        case 'Spades': return '♠';
        default: return '';
    }
}

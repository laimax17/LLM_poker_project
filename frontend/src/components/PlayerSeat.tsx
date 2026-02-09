import { motion } from 'framer-motion';
import type { Player, Card } from '../types';
import { useGameStore } from '../store/useGameStore';

interface Props {
    player: Player;
    position: 'bottom' | 'top' | 'left' | 'right'; // Simplified for 2-6 players
    isWinner?: boolean;
}

export const PlayerSeat: React.FC<Props> = ({ player, position, isWinner }) => {
    const { gameState, aiThought } = useGameStore();

    // Check if it's this player's turn
    const isTurn = gameState && gameState.players[gameState.current_player_idx].id === player.id && gameState.state !== 'SHOWDOWN' && gameState.state !== 'FINISHED';

    const isAI = player.id === 'ai';
    const showSpeech = isAI && aiThought && aiThought.chat;

    return (
        <div className={`flex flex-col items-center relative p-4 ${position === 'bottom' ? 'order-last' : ''}`}>

            {/* AI Speech Bubble */}
            {showSpeech && (
                <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0 }}
                    className="absolute -top-16 bg-cyber-neonPurple text-white text-xs p-2 rounded-lg border border-cyber-neonBlue max-w-[150px] z-20 shadow-[0_0_15px_rgba(188,19,254,0.5)]"
                >
                    {aiThought.chat}
                    <div className="absolute bottom-[-6px] left-1/2 -translate-x-1/2 w-3 h-3 bg-cyber-neonPurple rotate-45"></div>
                </motion.div>
            )}

            {/* Avatar Circle */}
            <div className={`w-16 h-16 rounded-full border-2 ${isWinner ? 'border-yellow-400 shadow-[0_0_30px_#fbbf24]' : player.is_active ? (isTurn ? 'border-yellow-500 shadow-[0_0_20px_#fbbf24] animate-pulse' : 'border-cyber-neonBlue shadow-[0_0_10px_#00f0ff]') : 'border-gray-600 opacity-50'} flex items-center justify-center bg-gray-800 relative`}>
                <span className="text-white font-orbitron font-bold text-xl">{player.name[0]}</span>
                {player.is_dealer && (
                    <div className="absolute -right-2 -bottom-2 w-6 h-6 bg-white rounded-full text-black flex items-center justify-center text-xs font-bold border border-black">D</div>
                )}
            </div>

            {/* Turn Progress Bar */}
            {isTurn && (
                <div className="w-16 h-1 bg-gray-700 mt-1 rounded-full overflow-hidden">
                    <motion.div
                        initial={{ width: '100%' }}
                        animate={{ width: '0%' }}
                        transition={{ duration: 15, ease: "linear" }}
                        className="h-full bg-yellow-500"
                    />
                </div>
            )}

            {/* Name & Chips */}
            <div className="mt-1 text-center bg-black/60 px-3 py-1 rounded backdrop-blur-sm border border-gray-700">
                <div className="text-sm font-bold text-white">{player.name}</div>
                <div className="text-xs text-cyber-neonBlue font-mono">${player.chips}</div>
            </div>

            {/* Cards */}
            <div className="flex gap-1 mt-2">
                {player.hand.map((card, idx) => (
                    <CardView key={idx} card={card || null} hidden={card === null} />
                ))}
            </div>

            {/* Current Bet */}
            {player.current_bet > 0 && (
                <div className="absolute top-1/2 -translate-y-1/2 -right-16 bg-black/40 text-cyber-neonBlue border border-cyber-neonBlue rounded px-2 py-1 text-xs">
                    Bet: {player.current_bet}
                </div>
            )}
        </div>
    );
};

// Card can be null if masked
const CardView = ({ card, hidden }: { card: Card | null, hidden?: boolean }) => {
    return (
        <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className={`w-10 h-14 rounded bg-white text-black flex flex-col items-center justify-center border ${hidden || !card ? 'bg-cyber-pattern' : ''}`}
        >
            {hidden || !card ? (
                <div className="w-full h-full bg-indigo-900 rounded border-2 border-white/20 flex items-center justify-center">
                    <div className="w-4 h-6 border border-white/10"></div>
                </div>
            ) : (
                <>
                    <span className={`text-sm font-bold ${['Hearts', 'Diamonds'].includes(card.suit) ? 'text-red-600' : 'text-black'}`}>
                        {getRankSymbol(card.rank)}
                    </span>
                    <span className={`text-[10px] leading-none ${['Hearts', 'Diamonds'].includes(card.suit) ? 'text-red-600' : 'text-black'}`}>
                        {getSuitSymbol(card.suit)}
                    </span>
                </>
            )}
        </motion.div>
    )
}

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

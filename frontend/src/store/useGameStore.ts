import { create } from 'zustand';
import { io, Socket } from 'socket.io-client';
import type { GameState, AIThought } from '../types';

interface GameStore {
  socket: Socket | null;
  gameState: GameState | null;
  aiThought: AIThought | null;
  isConnected: boolean;
  
  connect: () => void;
  startGame: () => Promise<void>;
  sendAction: (action: string, amount?: number) => void;
  startNextHand: () => void;
  copyPrompt: () => string;
}

export const useGameStore = create<GameStore>((set, get) => ({
  socket: null,
  gameState: null,
  aiThought: null,
  isConnected: false,

  connect: () => {
    const socket = io('http://localhost:8000');

    socket.on('connect', () => {
      set({ isConnected: true });
      console.log('Connected to backend');
    });

    socket.on('disconnect', () => {
      set({ isConnected: false });
    });

    socket.on('game_state', (data: GameState) => {
      set({ gameState: data });
    });

    socket.on('ai_thought', (data: AIThought) => {
      set({ aiThought: data });
    });

    set({ socket });
  },

  startGame: async () => {
    try {
      const res = await fetch('http://localhost:8000/start-game', { method: 'POST' });
      if (!res.ok) throw new Error('Failed to start game');
    } catch (e) {
      console.error(e);
    }
  },

  sendAction: (action: string, amount: number = 0) => {
    const { socket } = get();
    if (socket) {
      console.log('📡 Emitting event [player_action] to backend with payload:', { action, amount });
      socket.emit('player_action', { action, amount });
    }
  },

  startNextHand: () => {
    const { socket } = get();
    if (socket) {
        console.log('📡 Emitting event [start_next_hand]');
        socket.emit('start_next_hand', {});
    }
  },

  copyPrompt: () => {
    const state = get().gameState;
    if (!state) return "No game state";
    
    // Construct a helpful prompt for the user
    const me = state.players.find(p => p.id === 'human');
    if (!me) return "Player not found";
    
    const hand = me.hand.map(c => `${c.rank} of ${c.suit}`).join(', ');
    const comm = state.community_cards.map(c => `${c.rank} of ${c.suit}`).join(', ');
    
    return `I am playing Texas Hold'em. 
    My Hand: ${hand}
    Community Cards: ${comm}
    Pot: ${state.pot}
    My Chips: ${me.chips}
    Current Bet to Call: ${state.current_bet - me.current_bet}
    
    What should I do? Respond with logic.`;
  }
}));

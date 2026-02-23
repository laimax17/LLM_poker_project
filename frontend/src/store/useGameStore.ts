import { create } from 'zustand';
import { io, Socket } from 'socket.io-client';
import type {
  GameState,
  AICoachAdvice,
  BotThought,
  LLMConfig,
} from '../types';

const BACKEND_URL = 'http://localhost:8000';

interface GameStore {
  // Connection
  socket: Socket | null;
  isConnected: boolean;

  // Game state
  gameState: GameState | null;

  // Bot thoughts (speech bubbles per bot)
  botThoughts: Record<string, BotThought>;

  // AI Coach
  coachAdvice: AICoachAdvice | null;
  isRequestingAdvice: boolean;
  showCoach: boolean;

  // LLM Config
  llmConfig: LLMConfig;

  // Actions
  connect: () => void;
  startGame: () => Promise<void>;
  sendAction: (action: string, amount?: number) => void;
  startNextHand: () => void;
  requestAdvice: () => void;
  closeCoach: () => void;
  setLLMConfig: (config: Partial<LLMConfig>) => void;
}

export const useGameStore = create<GameStore>((set, get) => ({
  socket: null,
  isConnected: false,
  gameState: null,
  botThoughts: {},
  coachAdvice: null,
  isRequestingAdvice: false,
  showCoach: false,
  llmConfig: {
    engine: 'rule-based',
    model: '',
    status: 'online',
  },

  connect: () => {
    const socket = io(BACKEND_URL);

    socket.on('connect', () => {
      set({ isConnected: true });
    });

    socket.on('disconnect', () => {
      set({ isConnected: false });
    });

    socket.on('game_state', (data: GameState) => {
      set({ gameState: data });
    });

    socket.on('ai_thought', (data: BotThought) => {
      set(state => ({
        botThoughts: {
          ...state.botThoughts,
          [data.player_id]: data,
        },
      }));
    });

    socket.on('ai_advice', (data: AICoachAdvice) => {
      set({ coachAdvice: data, isRequestingAdvice: false, showCoach: true });
    });

    socket.on('llm_status', (data: { status: 'online' | 'offline' }) => {
      set(state => ({
        llmConfig: { ...state.llmConfig, status: data.status },
      }));
    });

    socket.on('error', (data: { message: string }) => {
      console.error('Backend error:', data.message);
    });

    set({ socket });
  },

  startGame: async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/start-game`, { method: 'POST' });
      if (!res.ok) throw new Error('Failed to start game');
    } catch (e) {
      console.error(e);
    }
  },

  sendAction: (action: string, amount = 0) => {
    const { socket } = get();
    if (socket) {
      socket.emit('player_action', { action, amount });
    }
  },

  startNextHand: () => {
    const { socket } = get();
    if (socket) {
      socket.emit('start_next_hand', {});
    }
  },

  requestAdvice: () => {
    const { socket, llmConfig } = get();
    if (!socket) return;
    set({ isRequestingAdvice: true, showCoach: true, coachAdvice: null });
    socket.emit('request_advice', { engine: llmConfig.engine, model: llmConfig.model });
  },

  closeCoach: () => {
    set({ showCoach: false });
  },

  setLLMConfig: (config: Partial<LLMConfig>) => {
    const { socket } = get();
    const newConfig = { ...get().llmConfig, ...config };
    set({ llmConfig: { ...newConfig, status: 'loading' } });
    if (socket) {
      socket.emit('set_llm_config', { engine: newConfig.engine, model: newConfig.model });
    }
  },
}));

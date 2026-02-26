import { create } from 'zustand';
import { io, Socket } from 'socket.io-client';
import type {
  GameState,
  AICoachAdvice,
  BotThought,
  LLMConfig,
} from '../types';
import {
  playCardDeal,
  playChipClink,
  playYourTurn,
  playWin,
  playFold,
} from '../utils/sound';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL ?? 'http://localhost:8000';

interface GameStore {
  // Connection
  socket: Socket | null;
  isConnected: boolean;

  // Game state
  gameState: GameState | null;

  // Bot thoughts (speech bubbles per bot)
  botThoughts: Record<string, BotThought>;

  // Error toast
  errorMessage: string | null;

  // Hand counter (increments each time a new hand starts)
  handCount: number;

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
  errorMessage: null,
  handCount: 0,
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
      // Fix 9: detect new hand start (FINISHED → PREFLOP transition)
      const prev = get().gameState;
      const isNewHand = prev?.state === 'FINISHED' && data.state === 'PREFLOP';

      // ── Sound triggers (compare prev vs incoming state) ──────────────────
      // New hand dealt
      if (isNewHand) {
        playCardDeal();
      }
      // Community cards revealed (flop/turn/river)
      else if ((data.community_cards.length ?? 0) > (prev?.community_cards.length ?? 0)) {
        playCardDeal();
      }
      // Pot grew — someone put chips in
      if (!isNewHand && (data.pot ?? 0) > (prev?.pot ?? 0)) {
        playChipClink();
      }
      // Human's turn just started
      const humanId = data.players[0]?.id;
      const wasHumanTurn = prev?.current_player_idx === 0 &&
        prev?.state !== 'SHOWDOWN' && prev?.state !== 'FINISHED';
      const isHumanTurnNow = data.current_player_idx === 0 &&
        data.state !== 'SHOWDOWN' && data.state !== 'FINISHED';
      if (!wasHumanTurn && isHumanTurnNow) {
        playYourTurn();
      }
      // Human wins
      const isShowdown = (data.state === 'SHOWDOWN' || data.state === 'FINISHED');
      const wasShowdown = prev?.state === 'SHOWDOWN' || prev?.state === 'FINISHED';
      if (isShowdown && !wasShowdown && humanId && data.winners.includes(humanId)) {
        playWin();
      }
      // ─────────────────────────────────────────────────────────────────────

      set(state => ({
        gameState: data,
        handCount: isNewHand ? state.handCount + 1 : state.handCount,
      }));
    });

    socket.on('ai_thought', (data: BotThought) => {
      set(state => ({
        botThoughts: {
          ...state.botThoughts,
          [data.player_id]: data,
        },
      }));
      // Two-step auto-clear: fade at 3.5 s, remove at 4 s.
      // Guard compares `chat` string so a newer thought is never cleared early.
      setTimeout(() => {
        set(state => {
          const existing = state.botThoughts[data.player_id];
          if (!existing || existing.chat !== data.chat) return state;
          return {
            botThoughts: {
              ...state.botThoughts,
              [data.player_id]: { ...existing, fading: true },
            },
          };
        });
      }, 3500);
      setTimeout(() => {
        set(state => {
          const existing = state.botThoughts[data.player_id];
          if (!existing || existing.chat !== data.chat) return state;
          const updated = { ...state.botThoughts };
          delete updated[data.player_id];
          return { botThoughts: updated };
        });
      }, 4000);
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
      // Fix 4: surface error in UI toast, auto-dismiss after 3 s
      set({ errorMessage: data.message });
      setTimeout(() => set({ errorMessage: null }), 3000);
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
      // Immediate audio feedback on human action
      if (action === 'fold') playFold();
      else playChipClink();
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

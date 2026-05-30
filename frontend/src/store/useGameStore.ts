import { create } from 'zustand';
import { io, Socket } from 'socket.io-client';
import type {
  GameState,
  AICoachAdvice,
  BotThought,
  LLMConfig,
  PlayerAction,
  LiveHint,
  HandReview,
  SessionStats,
  TournamentState,
  StandingEntry,
  EliminationEvent,
  GameSetupConfig,
  AllInEquity,
} from '../types';
import {
  playCardDeal,
  playChipClink,
  playChipStack,
  playYourTurn,
  playWin,
  playFold,
  prewarmAudio,
} from '../utils/sound';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL ?? 'http://localhost:8000';

interface GameOverData {
  reason: string;
  final_chips: number;
}

interface GameStore {
  // Connection
  socket: Socket | null;
  isConnected: boolean;

  // Game state
  gameState: GameState | null;

  // Bot thoughts (speech bubbles per bot)
  botThoughts: Record<string, BotThought>;

  // Bots currently waiting on LLM response (shows spinner)
  thinkingBots: Record<string, boolean>;

  // Error toast
  errorMessage: string | null;

  // Hand counter (increments each time a new hand starts)
  handCount: number;

  // AI Coach
  coachAdvice: AICoachAdvice | null;
  isRequestingAdvice: boolean;
  showCoach: boolean;

  // Floating action announcement
  currentAction: PlayerAction | null;

  // Action in-flight: true from sendAction until server responds (prevents double-click + stops blink)
  actionInFlight: boolean;

  // Game over
  isGameOver: boolean;
  gameOverReason: string | null;

  // LLM Config
  llmConfig: LLMConfig;

  // Learning Mode
  learningMode: boolean;
  liveHint: LiveHint | null;
  handReview: HandReview | null;
  sessionStats: SessionStats | null;
  showReview: boolean;
  showStats: boolean;

  // Tournament
  tournament: TournamentState | null;
  standings: StandingEntry[] | null;
  lastElimination: EliminationEvent | null;
  levelUpFlash: { level: number; smallBlind: number; bigBlind: number } | null;
  allinEquity: AllInEquity | null;

  // Actions
  connect: () => void;
  startGame: (config?: GameSetupConfig) => Promise<void>;
  sendAction: (action: string, amount?: number) => void;
  startNextHand: () => void;
  resetGame: (config?: GameSetupConfig) => void;
  closeStandings: () => void;
  requestAdvice: () => void;
  closeCoach: () => void;
  setLLMConfig: (config: Partial<LLMConfig>) => void;
  setLocale: (locale: string) => void;
  setLearningMode: (enabled: boolean) => void;
  closeReview: () => void;
  toggleStats: () => void;
}

export const useGameStore = create<GameStore>((set, get) => ({
  socket: null,
  isConnected: false,
  gameState: null,
  botThoughts: {},
  thinkingBots: {},
  errorMessage: null,
  handCount: 0,
  currentAction: null,
  actionInFlight: false,
  isGameOver: false,
  gameOverReason: null,
  coachAdvice: null,
  isRequestingAdvice: false,
  showCoach: false,
  llmConfig: {
    engine: 'rule-based',
    model: '',
    status: 'online',
  },
  learningMode: false,
  liveHint: null,
  handReview: null,
  sessionStats: null,
  showReview: false,
  showStats: false,
  tournament: null,
  standings: null,
  lastElimination: null,
  levelUpFlash: null,
  allinEquity: null,

  connect: () => {
    const socket = io(BACKEND_URL, {
      reconnectionDelay: 1000,
      reconnectionDelayMax: 10000,
      reconnectionAttempts: Infinity,
    });

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
        const potDelta = (data.pot ?? 0) - (prev?.pot ?? 0);
        if (potDelta >= 200) playChipStack(); // big bet/raise
        else playChipClink();
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
        actionInFlight: false,  // server responded → clear in-flight lock
        allinEquity: isNewHand ? null : state.allinEquity,
      }));
    });

    socket.on('ai_thought', (data: BotThought) => {
      // Use a unique token per message to avoid timer cross-fire when two
      // identical chat strings arrive close together.
      const token = `${data.player_id}:${Date.now()}`;
      set(state => ({
        botThoughts: {
          ...state.botThoughts,
          [data.player_id]: { ...data, _token: token } as BotThought & { _token: string },
        },
      }));
      // Two-step auto-clear: fade at 3.5 s, remove at 4 s.
      // Guard checks token so a newer thought is never cleared early.
      setTimeout(() => {
        set(state => {
          const existing = state.botThoughts[data.player_id] as (BotThought & { _token?: string }) | undefined;
          if (!existing || (existing as { _token?: string })._token !== token) return state;
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
          const existing = state.botThoughts[data.player_id] as (BotThought & { _token?: string }) | undefined;
          if (!existing || (existing as { _token?: string })._token !== token) return state;
          const updated = { ...state.botThoughts };
          delete updated[data.player_id];
          return { botThoughts: updated };
        });
      }, 4000);
    });

    socket.on('player_acted', (data: PlayerAction) => {
      // Skip if human action was already set locally in sendAction()
      if (data.player_id === 'human') return;
      set({ currentAction: data });
      setTimeout(() => {
        set(state => {
          if (state.currentAction === data) return { currentAction: null };
          return state;
        });
      }, 1500);
    });

    socket.on('game_over', (data: GameOverData) => {
      set({ isGameOver: true, gameOverReason: data.reason });
    });

    socket.on('ai_advice', (data: AICoachAdvice) => {
      set({ coachAdvice: data, isRequestingAdvice: false, showCoach: true });
    });

    socket.on('ai_thinking', (data: { player_id: string }) => {
      set(state => ({
        thinkingBots: { ...state.thinkingBots, [data.player_id]: true },
      }));
    });

    socket.on('ai_thinking_done', (data: { player_id: string }) => {
      set(state => {
        const updated = { ...state.thinkingBots };
        delete updated[data.player_id];
        return { thinkingBots: updated };
      });
    });

    // ── Learning Mode events ──
    socket.on('live_hint', (data: LiveHint) => {
      set({ liveHint: data });
    });

    socket.on('hand_review', (data: HandReview) => {
      // Only auto-open the review modal when there is something to learn from.
      set(state => ({
        handReview: data,
        showReview: state.learningMode && data.decisions.length > 0,
      }));
    });

    socket.on('session_stats', (data: SessionStats) => {
      set({ sessionStats: data });
    });

    // ── Tournament events ──
    socket.on('tournament_state', (data: TournamentState) => {
      set({ tournament: data });
    });

    socket.on('level_up', (data: { level: number; smallBlind: number; bigBlind: number }) => {
      set({ levelUpFlash: data });
      setTimeout(() => {
        set(state => (state.levelUpFlash === data ? { levelUpFlash: null } : state));
      }, 3500);
    });

    socket.on('player_eliminated', (data: EliminationEvent) => {
      set({ lastElimination: data });
      setTimeout(() => {
        set(state => (state.lastElimination === data ? { lastElimination: null } : state));
      }, 4000);
    });

    socket.on('tournament_over', (data: { standings: StandingEntry[] }) => {
      set({ standings: data.standings });
    });

    socket.on('allin_equity', (data: AllInEquity) => {
      set({ allinEquity: data });
      setTimeout(() => {
        set(state => (state.allinEquity === data ? { allinEquity: null } : state));
      }, 7000);
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

  startGame: async (config?: GameSetupConfig) => {
    prewarmAudio(); // initialize AudioContext during user gesture
    set({ isGameOver: false, gameOverReason: null, standings: null });
    try {
      const res = await fetch(`${BACKEND_URL}/start-game`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: config ? JSON.stringify(config) : undefined,
      });
      if (!res.ok) throw new Error('Failed to start game');
    } catch (e) {
      console.error(e);
    }
  },

  sendAction: (action: string, amount = 0) => {
    const { socket } = get();
    if (socket) {
      prewarmAudio(); // ensure context is running (idempotent)
      // Immediate audio feedback on human action
      if (action === 'fold') playFold();
      else if (amount >= 200) playChipStack();
      else playChipClink();

      // Immediate local action announcement for human
      const humanAction: PlayerAction = {
        player_id: 'human',
        player_name: 'PLAYER',
        action: action as PlayerAction['action'],
        amount,
      };
      // Clear the live hint immediately — it described the pre-action spot.
      set({ currentAction: humanAction, actionInFlight: true, liveHint: null });
      setTimeout(() => {
        set(state => {
          if (state.currentAction === humanAction) return { currentAction: null };
          return state;
        });
      }, 1500);

      socket.emit('player_action', { action, amount });
    }
  },

  startNextHand: () => {
    const { socket } = get();
    if (socket) {
      socket.emit('start_next_hand', {});
    }
  },

  resetGame: (config?: GameSetupConfig) => {
    const { socket } = get();
    if (socket) socket.emit('reset_game', config ?? {});
    set({
      isGameOver: false, gameOverReason: null, gameState: null, handCount: 0,
      botThoughts: {}, standings: null, tournament: null,
    });
  },

  closeStandings: () => set({ standings: null }),

  setLocale: (locale: string) => {
    const { socket } = get();
    if (socket) socket.emit('set_locale', { locale });
  },

  requestAdvice: () => {
    const { socket, llmConfig } = get();
    if (!socket) return;
    set({ isRequestingAdvice: true, showCoach: true, coachAdvice: null });
    socket.emit('request_advice', { engine: llmConfig.engine, model: llmConfig.model });
  },

  closeCoach: () => {
    set({ showCoach: false, isRequestingAdvice: false });
  },

  setLLMConfig: (config: Partial<LLMConfig>) => {
    const { socket } = get();
    const newConfig = { ...get().llmConfig, ...config };
    set({ llmConfig: { ...newConfig, status: 'loading' } });
    if (socket) {
      socket.emit('set_llm_config', { engine: newConfig.engine, model: newConfig.model });
    }
  },

  setLearningMode: (enabled: boolean) => {
    const { socket } = get();
    set({ learningMode: enabled });
    if (!enabled) set({ liveHint: null, showReview: false });
    if (socket) socket.emit('set_learning_mode', { enabled });
  },

  closeReview: () => set({ showReview: false }),

  toggleStats: () => set(state => ({ showStats: !state.showStats })),
}));

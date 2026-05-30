"""
FastAPI + Socket.IO main entry point for Cyber Hold'em backend.
"""
from __future__ import annotations

import asyncio
import logging
import os
import random
from typing import Any, Optional

import socketio
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .engine import PokerEngine
from .schemas import AIThought
from .ai.rule_based import RuleBasedStrategy
from .ai.llm_strategy import LLMBotStrategy
from .ai.coach import AICoach
from .ai.gto_strategy import GTOBotStrategy
from .ai.gto_coach import GTOCoach
from .ai.ollama import OllamaClient
from .ai.openai_client import OpenAICompatibleClient
from .ai.providers import (
    PROVIDERS,
    get_provider,
    models_payload,
    provider_api_key,
    provider_available,
)
from .ai.strategy import BotStrategy
from .ai.opponent_model import OpponentModel
from .ai.banter import get_banter
from .ai.showdown import equities_payload
from .learning import LearningTracker
from .tournament import TournamentManager, TournamentConfig

# Seed PRNG with OS entropy for unpredictable shuffles every server restart
random.seed(int.from_bytes(os.urandom(8), 'big'))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─── App setup ────────────────────────────────────────────────────────────────
app = FastAPI(title="Cyber Hold'em API")
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
socket_app = socketio.ASGIApp(sio, app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# ─── Bot personality assignments ──────────────────────────────────────────────
# Each bot gets a unique personality and display name.
BOT_PROFILES: list[dict[str, str]] = [
    {'id': 'bot_1', 'name': 'NEON',    'personality': 'shark'},
    {'id': 'bot_2', 'name': 'GRANITE', 'personality': 'rock'},
    {'id': 'bot_3', 'name': 'BLAZE',   'personality': 'maniac'},
    {'id': 'bot_4', 'name': 'GLACIER', 'personality': 'station'},
    {'id': 'bot_5', 'name': 'CIPHER',  'personality': 'tag'},
]

# ─── Per-bot thinking delay (seconds) tuned to personality ────────────────────
BOT_THINK_TIME: dict[str, tuple[float, float]] = {
    'bot_1': (1.2, 2.5),   # NEON    / shark   — balanced, calculated
    'bot_2': (1.5, 3.0),   # GRANITE / rock    — slow, deliberate (was 4.5s)
    'bot_3': (0.6, 1.5),   # BLAZE   / maniac  — fast, impulsive
    'bot_4': (1.2, 3.0),   # GLACIER / station — indecisive (was 4.0s)
    'bot_5': (1.0, 2.5),   # CIPHER  / tag     — moderate
}
_DEFAULT_THINK_TIME: tuple[float, float] = (1.0, 2.5)

# ─── Global state ─────────────────────────────────────────────────────────────
engine = PokerEngine()
_ai_lock = asyncio.Lock()  # Prevents concurrent bot decision loops
# Per-bot strategy dict (for rule-based mode, each bot has its own personality)
_bot_strategies: dict[str, BotStrategy] = {}
# Fallback single strategy (used for GTO/LLM where all bots share one)
_strategy: BotStrategy = RuleBasedStrategy()
_coach: Optional[AICoach | GTOCoach] = None
_llm_engine: str = os.environ.get('DEFAULT_AI_ENGINE', 'rule-based')
_llm_model: str = os.environ.get('LLM_MODEL', '')
_locale: str = 'en'  # current UI locale ('en' or 'zh'), affects bot chat language

# ─── Learning Mode state ──────────────────────────────────────────────────────
# Always-offline GTO coach used for live hints + decision grading, independent
# of the user-selected bot/coach engine (so hints work even on LLM engines).
_learning_mode: bool = False
_live_coach = GTOCoach()
_live_coach.N_SIM = 250  # fewer sims → snappier live hints; grading reuses the cache
_pending_hint: Optional[dict[str, Any]] = None  # GTO hint for the human's current turn
_tracker = LearningTracker()

# ─── Opponent modeling (agent memory) ─────────────────────────────────────────
# Tracks every player's tendencies across the session; fed to LLM bots so they
# can exploit reads. Always on (independent of learning mode).
_opponents = OpponentModel()
_hand_open: bool = False  # True between begin_hand and hand-end commit

# ─── Tournament ───────────────────────────────────────────────────────────────
_tournament = TournamentManager()
_pending_level_up: bool = False  # set when a hand starts at a new blind level

# ─── Living opponents (banter + tilt) ─────────────────────────────────────────
_BOT_PERSONALITY: dict[str, str] = {p['id']: p['personality'] for p in BOT_PROFILES}
_chips_at_hand_start: dict[str, int] = {}


# ─── Strategy factory ─────────────────────────────────────────────────────────
def _build_strategy(
    engine_name: str, model: str
) -> tuple[BotStrategy, AICoach | GTOCoach | None]:
    """Return (fallback_strategy, coach) pair for the given engine.

    `engine_name` is one of:
      - 'rule-based' / 'gto'  → offline bots + GTOCoach (no LLM)
      - 'ollama'              → local LLM via OllamaClient
      - any provider id in PROVIDERS (e.g. 'openrouter', 'deepseek')
                              → cloud LLM via the unified OpenAICompatibleClient

    LLM engines: bots use LLMBotStrategy, coach uses AICoach (LLM-powered).
    Offline engines: bots use GTOBotStrategy, coach uses GTOCoach so the human
    always has GTO hints even without an LLM.
    """
    if engine_name in ('gto', 'rule-based'):
        return GTOBotStrategy(), GTOCoach()

    if engine_name == 'ollama':
        spec = PROVIDERS['ollama']
        client = OllamaClient(model=model or spec.default_model)
        return LLMBotStrategy(client), AICoach(client)

    spec = get_provider(engine_name)
    if spec is not None:
        client = OpenAICompatibleClient(
            model=model or spec.default_model,
            base_url=spec.base_url,
            api_key=provider_api_key(engine_name),
        )
        return LLMBotStrategy(client), AICoach(client)

    # Unknown engine → safe offline default.
    logger.warning('Unknown engine %r, falling back to GTO', engine_name)
    return GTOBotStrategy(), GTOCoach()


def _rebuild_bot_strategies(engine_name: str, model: str) -> None:
    """Rebuild the per-bot strategy dict.

    For rule-based and gto: each bot gets its own GTOBotStrategy with a unique personality,
    combining GTO-optimal math with distinct character via personality modifiers.
    For LLM: all bots share the same LLMBotStrategy instance (no per-bot dict needed).
    """
    global _bot_strategies
    if engine_name in ('rule-based', 'gto'):
        _bot_strategies = {
            prof['id']: GTOBotStrategy(personality=prof['personality'])
            for prof in BOT_PROFILES
        }
    else:
        _bot_strategies = {}


# Initialise from env
_strategy, _coach = _build_strategy(_llm_engine, _llm_model)
_rebuild_bot_strategies(_llm_engine, _llm_model)


def _get_strategy(bot_id: str) -> BotStrategy:
    """Return the strategy for a specific bot (per-bot if rule-based, shared otherwise)."""
    return _bot_strategies.get(bot_id, _strategy)


# ─── Helpers ──────────────────────────────────────────────────────────────────
def _is_human_turn() -> bool:
    """True if it is the human's turn and the hand is still in progress."""
    if engine.state.value in ('SHOWDOWN', 'FINISHED'):
        return False
    try:
        return engine.players[engine.current_player_idx].id == 'human'
    except IndexError:
        return False


def _human_chips() -> int:
    human = next((p for p in engine.players if p.id == 'human'), None)
    return human.chips if human else 0


def _prepare_hand() -> None:
    """Advance the tournament and set the engine blinds BEFORE start_hand().

    The engine reads small_blind/big_blind inside start_hand(), so escalation
    happens here. Stores a pending level-up flag for broadcast_state to emit.
    """
    global _pending_level_up
    if _tournament.active:
        _pending_level_up = _tournament.on_hand_start()
        sb, bb = _tournament.current_blinds()
        engine.small_blind = sb
        engine.big_blind = bb


def _begin_hand() -> None:
    """Common per-hand setup for the learning tracker and opponent model."""
    global _hand_open, _chips_at_hand_start
    _tracker.begin_hand(_human_chips())
    _opponents.begin_hand()
    _chips_at_hand_start = {p.id: p.chips for p in engine.players}
    # Tilt cools off each hand.
    for strat in _bot_strategies.values():
        tilt = getattr(strat, 'tilt', 0.0)
        if tilt > 0:
            strat.tilt = tilt * 0.5 if tilt * 0.5 >= 0.1 else 0.0
    _hand_open = True


async def _settle_living_opponents() -> None:
    """At hand end: set tilt on big losers and emit reactive bot banter."""
    if not _chips_at_hand_start:
        return
    bb = max(1, engine.big_blind)
    events: list[tuple[int, str, str]] = []  # (priority, bot_id, event)
    for p in engine.players:
        if p.id == 'human':
            continue
        start = _chips_at_hand_start.get(p.id)
        if start is None:
            continue
        delta = p.chips - start
        if p.chips <= 0 and start > 0:
            events.append((3, p.id, 'eliminated'))
        elif delta >= max(start * 0.5, bb * 8):
            event = 'doubled_up' if p.chips >= start * 2 else 'won_big'
            events.append((2, p.id, event))
        elif delta <= -max(start * 0.4, bb * 6):
            events.append((1, p.id, 'lost_big'))
            strat = _bot_strategies.get(p.id)
            if strat is not None and hasattr(strat, 'tilt'):
                strat.tilt = min(1.0, strat.tilt + 0.8)
    # Emit at most two reactions, highest priority first, to avoid chat spam.
    events.sort(key=lambda e: e[0], reverse=True)
    for _prio, bot_id, event in events[:2]:
        line = get_banter(event, _BOT_PERSONALITY.get(bot_id, 'shark'), _locale)
        if line:
            await sio.emit('ai_thought', {'player_id': bot_id, 'thought': event, 'chat': line})


def _post_antes() -> None:
    """Post antes for the current blind level (tournament layer, no engine change).

    Antes are dead money: they go into the pot and each player's total_bet (so
    side pots stay correct) but are NOT a bet to call, so current_bet is left
    untouched and the normal betting round proceeds against the big blind.
    """
    ante = _tournament.current_ante() if _tournament.active else 0
    if ante <= 0:
        return
    for p in engine.players:
        if not p.is_active or p.chips <= 0:
            continue
        amt = min(p.chips, ante)
        p.chips -= amt
        p.total_bet += amt
        engine.pot += amt
        if p.chips == 0:
            p.is_all_in = True
    # If antes put the to-act player all-in, advance to the next able player.
    n = len(engine.players)
    guard = 0
    while n and engine.players[engine.current_player_idx].is_all_in and guard < n:
        engine.current_player_idx = (engine.current_player_idx + 1) % n
        guard += 1


def _players_summary() -> list[dict[str, Any]]:
    return [{'id': p.id, 'name': p.name, 'chips': p.chips} for p in engine.players]


async def _maybe_emit_allin_equity(board_before: list, street_before: str) -> None:
    """If the last action triggered an all-in run-out, emit each contestant's
    win% computed on the board *before* the run-out (broadcast-style drama)."""
    if engine.state.value not in ('SHOWDOWN', 'FINISHED'):
        return
    if len(engine.community_cards) <= len(board_before):
        return  # no cards were dealt by that action → not a run-out
    contestants = [
        (p.id, p.name, list(p.hand))
        for p in engine.players if p.is_active and len(p.hand) == 2
    ]
    if len(contestants) < 2:
        return
    try:
        payload = equities_payload(contestants, list(board_before))
        payload['street'] = street_before
        await sio.emit('allin_equity', payload)
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning('all-in equity computation failed: %s', exc)


def _observe(player_id: str, street: str, action: str) -> None:
    """Feed one observed action into the opponent model (always on)."""
    _opponents.observe(player_id, street, action)


async def _maybe_emit_live_hint(state: dict[str, Any]) -> None:
    """When learning mode is on and it's the human's turn, compute and emit a
    compact GTO hint (and cache it for grading the human's upcoming action)."""
    global _pending_hint
    if not _learning_mode or not _is_human_turn():
        return
    try:
        hint = await _live_coach.analyze(state, 'human')
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning('live hint analyze failed: %s', exc)
        return
    _pending_hint = hint
    await sio.emit('live_hint', {
        'recommendation': hint.get('recommendation'),
        'recommendedAmount': hint.get('recommendedAmount'),
        'stats': hint.get('stats', []),
        'isPreflop': state.get('state') == 'PREFLOP',
    })


async def _maybe_finalize_hand() -> None:
    """When learning mode is on and a hand has ended, emit the hand review and
    refreshed session stats."""
    if not _learning_mode:
        return
    if engine.state.value not in ('SHOWDOWN', 'FINISHED'):
        return
    review = _tracker.finalize_hand(_human_chips())
    if review is not None:
        await sio.emit('hand_review', review)
        await sio.emit('session_stats', _tracker.session_stats())


async def broadcast_state() -> None:
    """Emit game state (human POV + is_dealer augmentation) to all clients."""
    state = engine.get_public_game_state('human')
    total = len(engine.players)
    dealer_idx = engine.dealer_idx % total if total else 0
    for i, p_data in enumerate(state['players']):
        p_data['is_dealer'] = (i == dealer_idx)
    await sio.emit('game_state', state)

    # Check if human is eliminated after hand ends
    if engine.state.value in ('SHOWDOWN', 'FINISHED'):
        human = next((p for p in engine.players if p.id == 'human'), None)
        if human and human.chips <= 0:
            await sio.emit('game_over', {'reason': 'eliminated', 'final_chips': 0})

    # ── Tournament: live HUD state + level-up notice ──
    global _hand_open, _pending_level_up
    if _tournament.active:
        await sio.emit('tournament_state', _tournament.state_payload(_players_summary(), 'human'))
        if _pending_level_up:
            _pending_level_up = False
            sb, bb = _tournament.current_blinds()
            await sio.emit('level_up', {'level': _tournament.level + 1, 'smallBlind': sb, 'bigBlind': bb})

    # ── Commit opponent reads once per hand (always on) ──
    if _hand_open and engine.state.value in ('SHOWDOWN', 'FINISHED'):
        _opponents.commit_hand()
        _hand_open = False
        await _settle_living_opponents()
        await _settle_tournament_hand()

    # ── Learning Mode hooks ──
    await _maybe_finalize_hand()
    await _maybe_emit_live_hint(state)


async def _settle_tournament_hand() -> None:
    """At hand end: announce eliminations and detect tournament completion."""
    if not _tournament.active:
        return
    summary = _players_summary()
    for elim in _tournament.record_eliminations(summary):
        await sio.emit('player_eliminated', elim)
    if _tournament.is_over(summary):
        _tournament.active = False
        await sio.emit('tournament_over', {
            'standings': _tournament.final_standings(summary),
        })


async def check_ai_turn() -> None:
    """Drive bot turns until the human must act or the hand ends."""
    if _ai_lock.locked():
        return
    async with _ai_lock:
        while True:
            if engine.state.value in ('FINISHED', 'SHOWDOWN'):
                break
            try:
                current_p = engine.players[engine.current_player_idx]
            except IndexError:
                break

            if not (current_p.id.startswith('bot_') and current_p.is_active and not current_p.is_all_in):
                break

            think_lo, think_hi = BOT_THINK_TIME.get(current_p.id, _DEFAULT_THINK_TIME)
            await asyncio.sleep(random.uniform(think_lo, think_hi))
            state_for_bot = engine.get_public_game_state(current_p.id)

            strategy = _get_strategy(current_p.id)
            is_llm_call = isinstance(strategy, LLMBotStrategy)
            if is_llm_call:
                await sio.emit('ai_thinking', {'player_id': current_p.id})
            bot_street = state_for_bot.get('state', 'PREFLOP')
            try:
                if isinstance(strategy, LLMBotStrategy):
                    active_ids = [p.id for p in engine.players if p.is_active]
                    profiles = _opponents.profiles_except(current_p.id, only_active=active_ids)
                    decision = await strategy.decide_async(
                        state_for_bot, current_p.id, opponents=profiles
                    )
                elif isinstance(strategy, (RuleBasedStrategy, GTOBotStrategy)):
                    decision = strategy.decide(state_for_bot, current_p.id, locale=_locale)
                else:
                    decision = strategy.decide(state_for_bot, current_p.id)
            except Exception as exc:
                logger.error('Strategy.decide failed for %s: %s', current_p.id, exc)
                decision = AIThought(action='fold', amount=0, thought='error fallback', chat_message='...')
            finally:
                if is_llm_call:
                    await sio.emit('ai_thinking_done', {'player_id': current_p.id})

            if decision.chat_message:
                await sio.emit('ai_thought', {
                    'player_id': current_p.id,
                    'thought': decision.thought,
                    'chat': decision.chat_message,
                })

            actual_action = decision.action
            actual_amount = decision.amount
            board_before = list(engine.community_cards)
            street_before = engine.state.value
            try:
                engine.player_action(current_p.id, decision.action, decision.amount)
            except Exception as exc:
                logger.error('engine.player_action error %s (action=%s): %s', current_p.id, decision.action, exc)
                actual_action = 'fold'
                actual_amount = 0
                try:
                    engine.player_action(current_p.id, 'fold', 0)
                except Exception:
                    pass

            _observe(current_p.id, bot_street, actual_action)
            await _maybe_emit_allin_equity(board_before, street_before)

            await sio.emit('player_acted', {
                'player_id': current_p.id,
                'player_name': current_p.name,
                'action': actual_action,
                'amount': actual_amount,
            })
            await broadcast_state()


# ─── HTTP endpoints ────────────────────────────────────────────────────────────
@app.get('/')
def read_root() -> dict[str, str]:
    return {'status': 'ok', 'message': "Cyber Hold'em backend running"}


@app.get('/health')
async def health() -> dict[str, Any]:
    llm_ok: Optional[bool] = None
    if isinstance(_strategy, LLMBotStrategy):
        llm_ok = await _strategy.llm.health_check()
    return {
        'status': 'ok',
        'engine': _llm_engine,
        'model': _llm_model,
        'llm_connected': llm_ok,
    }


class StartGameRequest(BaseModel):
    num_opponents: int = 5
    starting_stack: int = 5000
    blind_speed: str = 'normal'
    difficulty: str = 'normal'


def _setup_new_tournament(req: StartGameRequest) -> None:
    """Build the table + (re)start the tournament from a setup request."""
    global _llm_engine, _strategy, _coach
    cfg = TournamentConfig(
        num_opponents=req.num_opponents,
        starting_stack=req.starting_stack,
        blind_speed=req.blind_speed,
        difficulty=req.difficulty,
    )
    _tournament.configure(cfg)
    cfg = _tournament.config  # sanitized

    # Difficulty selects the bot engine (LLMConfigBar can still override later).
    _llm_engine = _tournament.engine_for_difficulty()
    _strategy, _coach = _build_strategy(_llm_engine, _llm_model)
    _rebuild_bot_strategies(_llm_engine, _llm_model)

    engine.players = []
    engine.add_player('human', 'PLAYER', cfg.starting_stack)
    for prof in BOT_PROFILES[:cfg.num_opponents]:
        engine.add_player(prof['id'], prof['name'], cfg.starting_stack)

    _tracker.reset()
    _opponents.reset()
    _tournament.start(total_players=len(engine.players))


@app.post('/start-game')
async def start_game(config: StartGameRequest | None = None) -> dict[str, str]:
    _setup_new_tournament(config or StartGameRequest())
    _prepare_hand()
    engine.start_hand()
    _begin_hand()
    _post_antes()
    await broadcast_state()
    await check_ai_turn()
    return {'status': 'started'}


class AIConfigRequest(BaseModel):
    engine: str
    model: str


@app.get('/ai/config')
def get_ai_config() -> dict[str, str]:
    return {'engine': _llm_engine, 'model': _llm_model}


@app.get('/ai/models')
def get_ai_models() -> dict[str, Any]:
    """Return the provider + model registry for the LLMConfigBar dropdown."""
    return models_payload()


@app.post('/ai/config')
async def set_ai_config(config: AIConfigRequest) -> dict[str, str]:
    global _strategy, _coach, _llm_engine, _llm_model
    _llm_engine = config.engine
    _llm_model = config.model
    _strategy, _coach = _build_strategy(config.engine, config.model)
    _rebuild_bot_strategies(config.engine, config.model)
    logger.info('AI config updated via HTTP: engine=%s model=%s', config.engine, config.model)
    return {'status': 'ok', 'engine': _llm_engine, 'model': _llm_model}


# ─── Socket.IO events ─────────────────────────────────────────────────────────
@sio.event
async def player_action(sid: str, data: dict[str, Any]) -> None:
    logger.info('player_action from %s: %s', sid, data)
    try:
        action = data.get('action')
        amount = max(0, int(data.get('amount', 0)))
        current_player = engine.players[engine.current_player_idx]
        if current_player.id != 'human':
            await sio.emit('error', {'message': 'Not your turn!'}, to=sid)
            return

        # ── Learning Mode: grade this decision against the GTO baseline ──
        global _pending_hint
        if _learning_mode:
            pre_state = engine.get_public_game_state('human')
            hint = _pending_hint or await _live_coach.analyze(pre_state, 'human')
            _tracker.record_decision(hint, pre_state, action, amount)
            _pending_hint = None

        human_street = engine.state.value
        board_before = list(engine.community_cards)
        engine.player_action('human', action, amount)
        _observe('human', human_street, action)
        await _maybe_emit_allin_equity(board_before, human_street)
        await sio.emit('player_acted', {
            'player_id': 'human',
            'player_name': 'PLAYER',
            'action': action,
            'amount': amount,
        })
        await broadcast_state()
        await check_ai_turn()
    except Exception as exc:
        logger.error('player_action error: %s', exc)
        await sio.emit('error', {'message': str(exc)}, to=sid)


@sio.event
async def start_next_hand(sid: str, data: dict[str, Any]) -> None:
    logger.info('start_next_hand from %s', sid)
    try:
        _prepare_hand()
        engine.start_hand()
        _begin_hand()
        _post_antes()
        await broadcast_state()
        await check_ai_turn()
    except ValueError as exc:
        if 'Not enough players' in str(exc):
            logger.info('Game over: not enough players to continue')
            await sio.emit('game_over', {'reason': 'eliminated', 'final_chips': 0}, to=sid)
        else:
            logger.error('start_next_hand error: %s', exc)
            await sio.emit('error', {'message': str(exc)}, to=sid)
    except Exception as exc:
        logger.error('start_next_hand error: %s', exc)
        await sio.emit('error', {'message': str(exc)}, to=sid)


@sio.event
async def request_advice(sid: str, data: dict[str, Any]) -> None:
    logger.info('request_advice from %s: engine=%s', sid, data.get('engine'))
    global _strategy, _coach, _llm_engine, _llm_model

    req_engine = data.get('engine', _llm_engine)
    req_model = data.get('model', _llm_model)
    if req_engine != _llm_engine or req_model != _llm_model:
        _llm_engine = req_engine
        _llm_model = req_model
        _strategy, _coach = _build_strategy(req_engine, req_model)
        _rebuild_bot_strategies(req_engine, req_model)

    if _coach is None:
        if _locale == 'zh':
            _no_llm_body = '请先在 LLM 配置栏选择 Ollama 或 Qwen AI 引擎以使用 AI Coach。'
            _no_llm_label = '状态'
        else:
            _no_llm_body = 'Select an Ollama or Qwen engine in the LLM Config bar to use AI Coach.'
            _no_llm_label = 'Status'
        await sio.emit('ai_advice', {
            'recommendation': 'CHECK',
            'body': _no_llm_body,
            'stats': [{'label': _no_llm_label, 'value': 'NO LLM', 'quality': 'bad'}],
        }, to=sid)
        return

    try:
        state = engine.get_public_game_state('human')
        advice = await _coach.analyze(state, 'human')
        await sio.emit('ai_advice', advice, to=sid)
    except Exception as exc:
        logger.error('request_advice error: %s', exc)
        await sio.emit('ai_advice', {
            'recommendation': 'CHECK',
            'body': f'AI Coach 出错：{exc}',
            'stats': [{'label': '状态', 'value': 'ERROR', 'quality': 'bad'}],
        }, to=sid)


@sio.event
async def set_llm_config(sid: str, data: dict[str, Any]) -> None:
    global _strategy, _coach, _llm_engine, _llm_model
    engine_name = data.get('engine', 'rule-based')
    model = data.get('model', '')
    _llm_engine = engine_name
    _llm_model = model
    _strategy, _coach = _build_strategy(engine_name, model)
    _rebuild_bot_strategies(engine_name, model)
    logger.info('LLM config via socket: engine=%s model=%s', engine_name, model)

    if isinstance(_strategy, LLMBotStrategy):
        healthy = await _strategy.llm.health_check()
        await sio.emit('llm_status', {'status': 'online' if healthy else 'offline'}, to=sid)
    else:
        await sio.emit('llm_status', {'status': 'online'}, to=sid)


@sio.event
async def connect(sid: str, environ: dict[str, Any]) -> None:
    """On (re)connect, send current game state if a game is in progress."""
    logger.info('Client connected: %s', sid)
    if engine.players:
        await broadcast_state()


@sio.event
async def reset_game(sid: str, data: dict[str, Any]) -> None:
    """Full game reset — restart the tournament with the same (or new) config."""
    logger.info('reset_game from %s', sid)
    req = StartGameRequest(
        num_opponents=data.get('num_opponents', _tournament.config.num_opponents),
        starting_stack=data.get('starting_stack', _tournament.config.starting_stack),
        blind_speed=data.get('blind_speed', _tournament.config.blind_speed),
        difficulty=data.get('difficulty', _tournament.config.difficulty),
    )
    _setup_new_tournament(req)
    _prepare_hand()
    engine.start_hand()
    _begin_hand()
    _post_antes()
    await broadcast_state()
    await check_ai_turn()


@sio.event
async def set_learning_mode(sid: str, data: dict[str, Any]) -> None:
    """Enable/disable Learning Mode (live hints + post-hand review + stats)."""
    global _learning_mode
    _learning_mode = bool(data.get('enabled', False))
    logger.info('Learning mode set to %s by %s', _learning_mode, sid)
    if _learning_mode:
        # Emit a hint immediately if it's already the human's turn.
        await _maybe_emit_live_hint(engine.get_public_game_state('human'))
        await sio.emit('session_stats', _tracker.session_stats(), to=sid)


@sio.event
async def set_locale(sid: str, data: dict[str, Any]) -> None:
    """Set the UI locale (affects bot chat language)."""
    global _locale
    new_locale = data.get('locale', 'en')
    if new_locale in ('en', 'zh'):
        _locale = new_locale
        logger.info('Locale set to %s by %s', _locale, sid)


if __name__ == '__main__':
    uvicorn.run(socket_app, host='0.0.0.0', port=8000)

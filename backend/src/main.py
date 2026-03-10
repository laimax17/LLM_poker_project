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
from .ai.openrouter import OpenRouterClient
from .ai.strategy import BotStrategy

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
# Per-bot strategy dict (GTO fallback: each bot has its own personality)
_bot_strategies: dict[str, BotStrategy] = {}
# Shared strategy (LLM when OpenRouter key is set, otherwise GTO)
_strategy: BotStrategy = RuleBasedStrategy()
_coach: Optional[AICoach | GTOCoach] = None
_llm_model: str = os.environ.get('OPENROUTER_MODEL', '')
_locale: str = 'en'  # current UI locale ('en' or 'zh'), affects bot chat language


# ─── Strategy factory ─────────────────────────────────────────────────────────
def _build_strategy(
    model: str,
) -> tuple[BotStrategy, AICoach | GTOCoach]:
    """Return (strategy, coach) pair.

    If OPENROUTER_API_KEY is set: bots use LLMBotStrategy via OpenRouter,
    coach uses AICoach (LLM-powered).
    Otherwise: bots use GTOBotStrategy, coach uses GTOCoach (no LLM needed).
    """
    api_key = os.environ.get('OPENROUTER_API_KEY', '')
    if api_key:
        client = OpenRouterClient(model=model or None)
        return LLMBotStrategy(client), AICoach(client)
    # No API key → pure GTO fallback
    logger.info('No OPENROUTER_API_KEY set; using GTO strategy as fallback')
    return GTOBotStrategy(), GTOCoach()


def _rebuild_bot_strategies(is_llm: bool) -> None:
    """Rebuild the per-bot strategy dict.

    GTO mode: each bot gets its own GTOBotStrategy with a unique personality.
    LLM mode: all bots share the LLMBotStrategy instance (no per-bot dict needed).
    """
    global _bot_strategies
    if not is_llm:
        _bot_strategies = {
            prof['id']: GTOBotStrategy(personality=prof['personality'])
            for prof in BOT_PROFILES
        }
    else:
        _bot_strategies = {}


# Initialise from env
_strategy, _coach = _build_strategy(_llm_model)
_rebuild_bot_strategies(isinstance(_strategy, LLMBotStrategy))


def _get_strategy(bot_id: str) -> BotStrategy:
    """Return the strategy for a specific bot (per-bot if rule-based, shared otherwise)."""
    return _bot_strategies.get(bot_id, _strategy)


# ─── Helpers ──────────────────────────────────────────────────────────────────
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
            is_llm_call = isinstance(strategy, LLMBotStrategy) and state_for_bot.get('state') != 'PREFLOP'
            if is_llm_call:
                await sio.emit('ai_thinking', {'player_id': current_p.id})
            try:
                if isinstance(strategy, LLMBotStrategy):
                    decision = await strategy.decide_async(state_for_bot, current_p.id)
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
        'model': _llm_model,
        'llm_connected': llm_ok,
    }


@app.post('/start-game')
async def start_game() -> dict[str, str]:
    engine.players = []
    engine.add_player('human', 'PLAYER', 5000)
    for prof in BOT_PROFILES:
        engine.add_player(prof['id'], prof['name'], 5000)
    engine.start_hand()
    await broadcast_state()
    await check_ai_turn()
    return {'status': 'started'}


class AIConfigRequest(BaseModel):
    model: str


@app.get('/ai/config')
def get_ai_config() -> dict[str, str]:
    return {'model': _llm_model}


@app.post('/ai/config')
async def set_ai_config(config: AIConfigRequest) -> dict[str, str]:
    global _strategy, _coach, _llm_model
    _llm_model = config.model
    _strategy, _coach = _build_strategy(config.model)
    _rebuild_bot_strategies(isinstance(_strategy, LLMBotStrategy))
    logger.info('AI config updated via HTTP: model=%s', config.model)
    return {'status': 'ok', 'model': _llm_model}


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
        engine.player_action('human', action, amount)
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
        engine.start_hand()
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
    logger.info('request_advice from %s', sid)

    if _coach is None:
        if _locale == 'zh':
            _no_llm_body = '请先设置 OPENROUTER_API_KEY 环境变量以使用 AI Coach。'
            _no_llm_label = '状态'
        else:
            _no_llm_body = 'Set OPENROUTER_API_KEY environment variable to use AI Coach.'
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
    global _strategy, _coach, _llm_model
    model = data.get('model', '')
    _llm_model = model
    _strategy, _coach = _build_strategy(model)
    _rebuild_bot_strategies(isinstance(_strategy, LLMBotStrategy))
    logger.info('LLM config via socket: model=%s', model)

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
    """Full game reset — restart with fresh chips for all players."""
    logger.info('reset_game from %s', sid)
    engine.players = []
    engine.add_player('human', 'PLAYER', 5000)
    for prof in BOT_PROFILES:
        engine.add_player(prof['id'], prof['name'], 5000)
    engine.start_hand()
    await broadcast_state()
    await check_ai_turn()


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

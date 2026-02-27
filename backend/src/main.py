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
from .ai.qwen import QwenClient
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

# ─── Global state ─────────────────────────────────────────────────────────────
engine = PokerEngine()
_strategy: BotStrategy = RuleBasedStrategy()
_coach: Optional[AICoach | GTOCoach] = None
_llm_engine: str = os.environ.get('DEFAULT_AI_ENGINE', 'rule-based')
_llm_model: str = ''


# ─── Strategy factory ─────────────────────────────────────────────────────────
def _build_strategy(
    engine_name: str, model: str
) -> tuple[BotStrategy, AICoach | GTOCoach | None]:
    """Return (strategy, coach) pair for the given engine name.

    LLM engines: bots use LLMBotStrategy, coach uses AICoach (LLM-powered).
    GTO engine:  bots use GTOBotStrategy, coach uses GTOCoach (no LLM needed).
    Rule-based:  bots use RuleBasedStrategy, coach uses GTOCoach so the human
                 always has access to GTO hints even without an LLM.
    """
    if engine_name == 'ollama':
        client = OllamaClient(model=model or None)
        return LLMBotStrategy(client), AICoach(client)
    if engine_name in ('qwen-plus', 'qwen-max'):
        client = QwenClient(model=model or engine_name)
        return LLMBotStrategy(client), AICoach(client)
    if engine_name == 'gto':
        return GTOBotStrategy(), GTOCoach()
    # 'rule-based' (default): bots use heuristics, human still gets GTO hints
    return RuleBasedStrategy(), GTOCoach()


# Initialise from env
_strategy, _coach = _build_strategy(_llm_engine, _llm_model)


# ─── Helpers ──────────────────────────────────────────────────────────────────
async def broadcast_state() -> None:
    """Emit game state (human POV + is_dealer augmentation) to all clients."""
    state = engine.get_public_game_state('human')
    total = len(engine.players)
    dealer_idx = engine.dealer_idx % total if total else 0
    for i, p_data in enumerate(state['players']):
        p_data['is_dealer'] = (i == dealer_idx)
    await sio.emit('game_state', state)


async def check_ai_turn() -> None:
    """Drive bot turns until the human must act or the hand ends."""
    while True:
        if engine.state.value in ('FINISHED', 'SHOWDOWN'):
            break
        try:
            current_p = engine.players[engine.current_player_idx]
        except IndexError:
            break

        if not (current_p.id.startswith('bot_') and current_p.is_active and not current_p.is_all_in):
            break

        await asyncio.sleep(random.uniform(0.5, 1.2))
        state_for_bot = engine.get_public_game_state(current_p.id)

        try:
            if isinstance(_strategy, LLMBotStrategy):
                decision = await _strategy.decide_async(state_for_bot, current_p.id)
            else:
                decision = _strategy.decide(state_for_bot, current_p.id)
        except Exception as exc:
            logger.error('Strategy.decide failed for %s: %s', current_p.id, exc)
            decision = AIThought(action='fold', amount=0, thought='error fallback', chat_message='...')

        if decision.chat_message:
            await sio.emit('ai_thought', {
                'player_id': current_p.id,
                'thought': decision.thought,
                'chat': decision.chat_message,
            })

        try:
            engine.player_action(current_p.id, decision.action, decision.amount)
        except Exception as exc:
            logger.error('engine.player_action error %s (action=%s): %s', current_p.id, decision.action, exc)
            try:
                engine.player_action(current_p.id, 'fold', 0)
            except Exception:
                pass

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


@app.post('/start-game')
async def start_game() -> dict[str, str]:
    engine.players = []
    engine.add_player('human', 'PLAYER', 5000)
    for i in range(1, 6):
        engine.add_player(f'bot_{i}', f'BOT-{i}', 5000)
    engine.start_hand()
    await broadcast_state()
    await check_ai_turn()
    return {'status': 'started'}


class AIConfigRequest(BaseModel):
    engine: str
    model: str


@app.get('/ai/config')
def get_ai_config() -> dict[str, str]:
    return {'engine': _llm_engine, 'model': _llm_model}


@app.post('/ai/config')
async def set_ai_config(config: AIConfigRequest) -> dict[str, str]:
    global _strategy, _coach, _llm_engine, _llm_model
    _llm_engine = config.engine
    _llm_model = config.model
    _strategy, _coach = _build_strategy(config.engine, config.model)
    logger.info('AI config updated via HTTP: engine=%s model=%s', config.engine, config.model)
    return {'status': 'ok', 'engine': _llm_engine, 'model': _llm_model}


# ─── Socket.IO events ─────────────────────────────────────────────────────────
@sio.event
async def player_action(sid: str, data: dict[str, Any]) -> None:
    logger.info('player_action from %s: %s', sid, data)
    try:
        action = data.get('action')
        amount = int(data.get('amount', 0))
        current_player = engine.players[engine.current_player_idx]
        if current_player.id != 'human':
            await sio.emit('error', {'message': 'Not your turn!'}, to=sid)
            return
        engine.player_action('human', action, amount)
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

    if _coach is None:
        await sio.emit('ai_advice', {
            'recommendation': 'CHECK',
            'body': '请先在 LLM 配置栏选择 Ollama 或 Qwen AI 引擎以使用 AI Coach。',
            'stats': [{'label': '状态', 'value': 'NO LLM', 'quality': 'bad'}],
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
    logger.info('LLM config via socket: engine=%s model=%s', engine_name, model)

    if isinstance(_strategy, LLMBotStrategy):
        healthy = await _strategy.llm.health_check()
        await sio.emit('llm_status', {'status': 'online' if healthy else 'offline'}, to=sid)
    else:
        await sio.emit('llm_status', {'status': 'online'}, to=sid)


if __name__ == '__main__':
    uvicorn.run(socket_app, host='0.0.0.0', port=8000)

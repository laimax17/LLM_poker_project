from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import socketio
import uvicorn
import asyncio
import random
from .engine import PokerEngine, Player
from .ai_service import AIAgent
from .schemas import ActionRequest, GameStateModel, PlayerModel

# Initialize FastAPI and Socket.IO
app = FastAPI()
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
socket_app = socketio.ASGIApp(sio, app)

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Game State
engine = PokerEngine()
ai_agent: Optional[AIAgent] = None

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Poker Backend Running"}

@app.post("/start-game")
async def start_game():
    global ai_agent
    try:
        engine.players = []
        # Human at Seat 0 (Bottom)
        engine.add_player("human", "Player (You)", 1000)
        
        # 5 AI Bots
        for i in range(1, 6):
            engine.add_player(f"bot_{i}", f"Bot {i}", 1000)
        
        # Initialize AI Agent (Singleton for now, or we can make one per bot)
        # For simple logic, one instance is fine if it just processes state.
        ai_agent = AIAgent("ai", mode="simple", personality="Aggressive") 
        
        engine.start_hand()
        await broadcast_state()
        
        # Trigger first turn
        await check_ai_turn()
        return {"status": "started"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

async def check_ai_turn():
    # Loop continuously while it's ANY bot's turn
    while True:
        try:
             # Get current game state to check who's turn it is
             # We need 'internal' state to know who is acting, but engine.get_public_game_state masks it?
             # Engine state properties are accessible directly on `engine`.
             if engine.state.value == "FINISHED":
                 break
                 
             current_p = engine.players[engine.current_player_idx]
        except IndexError:
             break 
             
        # If current player is a BOT (starts with 'bot_')
        if current_p.id.startswith("bot_") and current_p.is_active and not current_p.is_all_in:
            # Simulate Thinking Delay
            delay = random.uniform(0.5, 1.0)
            await asyncio.sleep(delay)
            
            # Get State specific to THIS bot (so it sees its own cards)
            # engine.get_public_game_state(current_p.id)
            # But wait, our `AIAgent` is initialized with `player_id="ai"`.
            # We need to pass the dynamic ID to `decide`.
            # Or make a new agent instance?
            # Let's just update the agent's ID or pass it.
            # `ai_service.py` uses `self.player_id` in `decide`. 
            # We should probably instantiate a new agent or change `decide` signature.
            # Easier: Just modify `decide` to accept `player_id` or set it on the fly.
            ai_agent.player_id = current_p.id
            
            # Get state for THIS bot
            state_for_bot = engine.get_public_game_state(current_p.id)
            
            decision = ai_agent.decide(state_for_bot)
            
            # Broadcast "thinking" or "chat" if desired (optional)
            if decision.chat_message:
                await sio.emit("ai_thought", {
                    "player_id": current_p.id,
                    "thought": decision.thought,
                    "chat": decision.chat_message
                })
            
            try:
                engine.player_action(current_p.id, decision.action, decision.amount)
            except Exception as e:
                print(f"Bot {current_p.id} Action Error: {e}")
                # Fallback
                try:
                    engine.player_action(current_p.id, "fold", 0)
                except:
                    pass
            
            await broadcast_state()
        else:
            # Human turn or game over
            break

@sio.event
async def player_action(sid, data):
    # data: {"action": "fold|call|raise", "amount": <int>}
    print(f"📥 Backend received [player_action] event. Data: {data}")
    try:
        # Validate input
        # req = ActionRequest(**data) # Strict validation
        action = data.get("action")
        amount = data.get("amount", 0)
        
        current_player = engine.players[engine.current_player_idx]
        print(f"🔍 Turn Check - Current Player: {current_player.id} ({current_player.name})")
        
        # Human turn check
        # For 6-Max, we must ensure it IS the human's turn.
        # Ideally we map sid to player_id, but for now we hardcode "human".
        if current_player.id != "human":
             print(f"⛔ Rejected: It is Player {current_player.id}'s turn, but 'human' tried to act.")
             await sio.emit("error", {"message": "Not your turn!"}, to=sid)
             return

        # Human turn?
        # For MVP, assume 'human' ID is mapped to socket user.
        print(f"✅ Executing Human Action: {action}, Amount: {amount}")
        engine.player_action("human", action, amount)
        await broadcast_state()

        # If it's now AI's turn, trigger AI
        await check_ai_turn()
        
    except Exception as e:
        print(f"❌ Action Error: {e}")
        await sio.emit("error", {"message": str(e)}, to=sid)
@sio.event
async def start_next_hand(sid, data):
    print(f"🔄 Starting Next Hand requested by {sid}")
    try:
        engine.start_hand()
        await broadcast_state()
        
        # Trigger AI if it's their turn (e.g. SB/BB logic)
        await check_ai_turn()
    except Exception as e:
        print(f"❌ Next Hand Error: {e}")
        await sio.emit("error", {"message": str(e)}, to=sid)

async def broadcast_state():
    # We broadcast the "Human Perspective" to everyone for now (since only 1 human)
    state = engine.get_public_game_state("human")
    await sio.emit("game_state", state)

if __name__ == "__main__":
    uvicorn.run(socket_app, host="0.0.0.0", port=8000)

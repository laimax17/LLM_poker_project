# Cyber Hold'em: 6-Max AI Poker Web App

A cyberpunk-themed Texas Hold'em application featuring a 6-player table (1 Human vs 5 Bots).

> **Note:** Bots default to a fast offline GTO+personality engine. Switch the
> engine to a cloud provider (OpenRouter / DeepSeek) or local Ollama in the in-game
> LLMConfigBar to enable LLM-powered agent bots. A built-in **Learning Mode**
> (live GTO hints, post-hand grading, leak detection) helps you study while you play.

## 🚀 Features

- **6-Max Table**: Authentic 6-player ring game experience.
- **Fast-Paced AI**: Rule-based bots play quickly (0.5s - 1.0s thinking time) to keep the action moving.
- **Cyberpunk UI**:
    -   **Hexagonal Layout**: Human player always centered at the bottom.
    -   **Turn Indicators**: Pulsing glow and countdown bar for active players.
    -   **Showdown Overlay**: Toggleable results screen to inspect the board and winning hands.
- **Game Engine**: Custom Python 3.9 poker engine handling pot distribution, side pots, and hand evaluation.
- **Dockerized**: One-click deployment for both frontend and backend.

## 🛠 Tech Stack

- **Frontend**: React (Vite), TypeScript, Tailwind CSS, Framer Motion, Zustand.
- **Backend**: Python 3.9 (FastAPI), Socket.IO, Pydantic.
- **Infrastructure**: Docker, Docker Compose, Nginx.

## 🏁 Quick Start

### 🐋 New to Docker?
If you don't have Docker installed, follow these steps first:
1.  **Download Docker Desktop**: Go to [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop) and download for your OS (Mac/Windows/Linux).
2.  **Install & Run**: Install the application and open it. Wait for the engine to start (the whale icon in your taskbar should stop animating).
3.  **Verify**: Open a terminal and run `docker --version`. If it prints a version number, you're ready!

### Run with Docker (Recommended)

1. **Start Services**
   Open your terminal in the project folder and run:
   ```bash
   docker-compose up --build
   ```
   *This command downloads all dependencies and starts the app. It may take a few minutes the first time.*

2. **Play**
   Open [http://localhost:3000](http://localhost:3000) in your browser.
   The backend API runs on [http://localhost:8000](http://localhost:8000).

3. **Stop the App**
   Press `Ctrl+C` in the terminal to stop the server.

### Gameplay Controls
-   **Fold/Check/Call/Raise**: Standard poker actions.
-   **Next Hand**: Manually trigger the next hand after a showdown.
-   **View Board**: Toggle the results modal to see the cards at the end of a hand.

## 🔮 Roadmap / TODO

The following features are planned but not yet enabled:

- [ ] **LLM Integration**: Re-enable the AI Persona system (ChatGPT/Claude) for chat banter and complex bluffing strategies.
- [ ] **Multiplayer Mode**: Allow multiple human players to join via WebSocket.
- [ ] **User Accounts**: persistent chip counts, statistics, and hand history.
- [ ] **Advanced Settings**: Configurable blind structures, starting chips, and difficulty levels.
- [ ] **Sound Effects**: Audio cues for chips, cards, and turns.

## 🤖 AI 引擎配置

游戏的 AI 引擎可在游戏内 LLMConfigBar 实时切换。云端 provider 全部走统一的
OpenAI 兼容客户端——**每个 provider 只需一个 API key，切模型只改一个下拉框**：

| 引擎 | 说明 | 需要网络 / Key |
|------|------|----------------|
| `rule-based` | 5 种人格规则 Bot，开箱即用 | 否 |
| `gto` | 位置 + 蒙特卡洛 GTO Bot | 否 |
| `ollama` | 本地 LLM 推理（Qwen/Llama）| 否（本机推理）|
| `openrouter` | 一个 key 访问 GPT / Claude / Gemini / DeepSeek / Qwen / Llama | `OPENROUTER_API_KEY` |
| `deepseek` | DeepSeek 直连，最便宜；deepseek-chat / reasoner | `DEEPSEEK_API_KEY` |

> LLM Bot 是**增强提示 + 对手记忆**型 agent：翻后会拿到预先算好的胜率、底池赔率、
> 位置、牌面质地，以及对手画像（VPIP/PFR/激进度 → LAG/TAG/station/rock），
> 据此做 +EV 决策。翻前走规则引擎以保证速度。

在 `backend/.env` 填入你拥有的 key 即可（见 `backend/.env.example`），未配置 key
的 provider 在 UI 中显示为 `NO KEY`。新增模型 = 在 `backend/src/ai/providers.py`
的 `MODELS` 里加一行。

---

## 🧪 Testing

The project includes unit tests for the poker logic.

```bash
# Run backend tests
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pytest tests/test_poker_logic.py
```

## 🤖 AI Assistance (Manual)
Click the **"AI Help: Copy Prompt"** button in the game UI to copy the current game state (Hand, Community Cards, Pot Odds) as a prompt. You can paste this into ChatGPT or Claude to get real-time strategy advice!

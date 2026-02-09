# Cyber Hold'em: Modern AI Poker Web App

A cyberpunk-themed Texas Hold'em application featuring dual-mode AI opponents (Algorithm & LLM Persona) and real-time multiplayer architecture.

## 🚀 Features

- **Dual-Mode AI**: Switch between "Algorithmic" (Pot Odds/EV) and "LLM Persona" (Bluffing/Banter) strategies.
- **Cyberpunk UI**: Neon aesthetics, dark mode, and smooth physics-based card animations using Framer Motion.
- **Engineered Logic**: Python 3.9 backend with pure Python poker engine (no `match-case` for compatibility).
- **Dockerized**: One-click deployment for both frontend and backend.

## 🛠 Tech Stack

- **Frontend**: React (Vite), TypeScript, Tailwind CSS, Framer Motion, Zustand.
- **Backend**: Python 3.9 (FastAPI), Socket.IO, Pydantic.
- **Infrastructure**: Docker, Docker Compose, Nginx (prod).

## 🏁 Quick Start

### Prerequisites
- Docker & Docker Compose
- (Optional) OpenAI/Anthropic API Key for LLM Mode.

### Run with Docker (Recommended)

1. **Set API Key (Optional)**
   Create a `.env` file in the root or export the variable:
   ```bash
   export LLM_API_KEY=your_api_key_here
   ```

2. **Start Services**
   ```bash
   docker-compose up --build
   ```

3. **Play**
   Open [http://localhost:3000](http://localhost:3000) in your browser.
   The backend API runs on [http://localhost:8000](http://localhost:8000).

### Local Development

**Backend**:
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn src.main:app --reload
```

**Frontend**:
```bash
cd frontend
npm install
npm run dev
```

## 🧪 Testing

The project includes comprehensive unit tests for the poker logic.

```bash
# Run backend tests
cd backend
pytest tests/test_poker_logic.py
```

## 🤖 AI Assistance
Click the **"AI Help: Copy Prompt"** button in the game UI to copy the current game state (Hand, Community Cards, Pot Odds) as a prompt optimized for ChatGPT/Clause to get real-time strategy advice.

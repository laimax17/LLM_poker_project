# CLAUDE.md — Cyber Hold'em Project Rules

> Claude Code 每次启动都必须先读这个文件。

## 项目概述
这是一个赛博朋克风格的 Texas Hold'em 扑克 Web 应用。
1 个人类玩家 vs 5 个 AI Bot，支持本地 Ollama 和云端 Qwen API 两种 AI 引擎。

## 技术栈（不可更改）
- Frontend: React + TypeScript + Vite + Tailwind CSS + Framer Motion + Zustand
- Backend: Python 3.9 + FastAPI + python-socketio + Pydantic
- Infrastructure: Docker + Docker Compose + Nginx
- AI: Ollama（本地）/ 阿里云 DashScope Qwen API（云端）

## 目录结构规范
```
frontend/src/
  components/
    card/          # Card 组件（Card.tsx, CardBack.tsx）
    player/        # PlayerBox.tsx, HumanPanel.tsx
    table/         # PokerTable.tsx, CommunityCards.tsx, PotDisplay.tsx
    ai-coach/      # AICoachPanel.tsx, InlineCard.tsx
    layout/        # ActionBar.tsx, LLMConfigBar.tsx
  store/           # Zustand stores
  types/           # 共享 TypeScript 类型
  hooks/           # 自定义 hooks

backend/
  poker_logic.py   # 扑克引擎（不要动）
  main.py          # FastAPI + Socket.IO
  ai/
    strategy.py    # BotStrategy 抽象基类
    rule_based.py  # RuleBasedStrategy
    llm_client.py  # LLMClient 抽象接口
    ollama.py      # OllamaClient
    qwen.py        # QwenClient（DashScope）
```

## 编码规范
- TypeScript: 严格类型，禁止 `any`，所有 Socket.IO 事件必须有共享类型定义
- Python: 使用 `logging` 模块，禁止 `print()`，所有函数必须有类型注解
- 组件: 每个组件单文件，props 必须有 TypeScript interface
- 环境变量: 敏感信息（API Key）必须通过 `.env` 文件注入，禁止硬编码

## 视觉规范（最高优先级）
- 视觉基准文件在 `design_reference/` 目录，任何 UI 实现必须对照这些文件
- 设计 token 定义在 `design_reference/tokens.css`，必须提取为 Tailwind 配置或 CSS 变量
- 牌面组件规格见 `design_reference/card_v3.html`
- 整体布局规格见 `design_reference/layout_v3.html`
- 字体: Georgia（牌面 rank）/ Silkscreen（UI 标题）/ VT323（AI 对话文本）/ Press Start 2P（按钮/标签）

## 禁止事项
- 禁止修改 `backend/poker_logic.py` 的核心逻辑
- 禁止使用 `any` 类型
- 禁止硬编码 API Key
- 禁止使用 `print()` 替代 logging
- 禁止在没有视觉基准对照的情况下自行发明 UI 样式

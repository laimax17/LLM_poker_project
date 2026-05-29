# Game-Feel Plan — 让 Cyber Hold'em 更像真实游戏

> 目标：从"技术 demo"升级为有结构、有进展、对手是活的、关键时刻有戏剧性的真实扑克游戏。
> 用户选择：**核心 = 锦标赛**；调味 = 摊牌戏剧性 + 进展与留存 + 赛前设置大厅 + 活的对手（全选）。

## 设计原则
- **不修改 `engine.py` 核心逻辑**（CLAUDE.md 禁令）。锦标赛靠在 `start_hand()` 前设置
  `engine.small_blind/big_blind`（可变属性）+ 一个新的 `tournament.py` 管理层实现。
- 复用已有：`equity.py`（全下胜率）、`opponent_model.py`（对手画像/上头）、聊天事件管线、
  showdown 揭牌（引擎已支持）、淘汰逻辑（chips==0 → inactive，<2 人 → "Not enough players"）。
- 单机本地游戏：**进展/留存用前端 localStorage**（容器是临时的，后端文件持久化无意义）。

---

## Phase 1 — 锦标赛引擎（后端） ★核心
`backend/src/tournament.py` 新增 `TournamentManager`：
- **配置**：`num_opponents(1-5)`、`starting_stack`、`blind_speed`(turbo/normal/slow = 每级 5/10/20 手)、`difficulty`→引擎。
- **盲注表**：`[(10,20),(15,30),(25,50),(50,100),(75,150),(100,200),(150,300),(200,400),(300,600),(500,1000),(750,1500),(1000,2000)]`，到顶后保持。
- **等级**：`level = hand_count // hands_per_level`，每手开始时推进，返回 `level_up` 标志。
- **名次**：每手结束扫描新破产玩家，按淘汰顺序记入 `standings`（淘汰名次 = 当时存活人数）。
- **结束**：存活 < 2 → 锦标赛结束，产出最终排名（冠军 + 倒序淘汰表）。
- `state_payload()`：level、sb/bb、距下一级手数、存活人数、你的当前排名。

`main.py` 接线：
- `POST /start-game` 接收可选 JSON 配置（Pydantic，带默认值，向后兼容）→ 配置锦标赛、按人数/筹码重建座位、设 0 级盲注。
- `_begin_hand()` 里：`on_hand_start()` → 设引擎盲注 → emit `tournament_state`（+ `level_up` 事件）。
- `broadcast_state()` 手牌结束处：记录淘汰 → emit `player_eliminated`（含名次）→ 若结束 emit `tournament_over`（最终排名）。

## Phase 2 — 赛前设置大厅 + 锦标赛 HUD（前端）
- **设置大厅**（开始游戏前）：对手数量、起始筹码、盲注速度、难度。`store.startGame(config)` 传给后端。
- **HUD**（牌桌顶部）：当前盲注级别 + 距升盲倒计时、存活人数、你的排名；升盲闪光提示。
- **淘汰 Toast**：「GRANITE 第 5 名出局」。
- **最终排名屏**：冠军/你的名次 + 重新开赛按钮。
- 文件：`components/lobby/SetupLobby.tsx`、`components/table/TournamentHUD.tsx`、`components/table/StandingsModal.tsx`；types/store/locales 扩展。

## Phase 3 — 摊牌戏剧性（前端为主 + 后端胜率）
- 后端：检测全下对局（≥2 人全下且下注结束）→ 用 `estimate_equity` 算各家胜率 → emit `allin_equity`。
- 前端：全下胜率条、公共牌慢速逐张翻开、牌型大字播报（「FULL HOUSE!」）、赢池筹码动画、爆冷高亮。

## Phase 4 — 活的对手（后端）
- 事件驱动台词：破产/翻倍/诈唬被抓/吃到爆冷/连输上头。复用聊天管线 emit `ai_thought`。
- **上头(tilt)**：刚输大池的 bot 临时放松（提高入池），由 `opponent_model` 标记 + 传给策略。

## Phase 5 — 进展与留存（前端 localStorage）
- 保存每次锦标赛结果、生涯统计（参赛/夺冠/平均名次/盈亏）、成就（首胜、逆袭、连胜等）。
- 「生涯」面板展示。

---

## 验证
- 后端：`pytest backend/tests/`（新增 `test_tournament.py`：盲注升级、名次记录、结束判定）。
- 运行时：启动后端，socket 跑完整锦标赛，确认 `tournament_state`/`level_up`/`player_eliminated`/`tournament_over` 正确。
- 前端：`tsc -b && vite build`。

## 交付顺序
Phase 1 → 2（核心可玩） → 3（戏剧性） → 4（活对手） → 5（留存）。每阶段独立测试 + 提交到
`claude/holdem-poker-analysis-EmXm3`。

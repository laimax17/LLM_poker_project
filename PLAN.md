# Cyber Hold'em — 改进计划

> 生成日期：2026-03-02
> 所有改动基于代码审查结论，按优先级分级执行。

---

## P0 — 立即修复（游戏可玩性/安全）

### P0-1 · `engine.py:270` — `_advance_turn` off-by-one
**文件**：`backend/src/engine.py`
**问题**：`while steps <= len(self.players)` 多循环一次，当所有玩家 all-in 时 `current_player_idx` 落错位置。
**改动**：
```python
# 改前
while steps <= len(self.players):
# 改后
while steps < len(self.players):
```

---

### P0-2 · `engine.py:286-289` — `_next_street` 无步数限制
**文件**：`backend/src/engine.py`
**问题**：`_next_street` 内 while 循环只靠 `all(is_all_in ...)` 一个出口，边缘情况下死循环。
**改动**：加 `steps` 计数器，超出 `len(players)` 次后强制 break。

---

### P0-3 · `main.py:262` — 前端 amount 未校验负数
**文件**：`backend/src/main.py`
**问题**：`amount = int(data.get('amount', 0))` 接受负数，负数经 `_place_bet_logic` 会导致筹码增加。
**改动**：
```python
amount = max(0, int(data.get('amount', 0)))
```

---

### P0-4 · `main.py:146-201` — `check_ai_turn()` 缺并发锁
**文件**：`backend/src/main.py`
**问题**：`player_action`、`start_next_hand`、`reset_game` 均调用 `check_ai_turn()`，快速点击或网络重连时触发并发决策，引擎报 `Not your turn`。
**改动**：新增模块级 `asyncio.Lock`，`check_ai_turn` 入口处 `if _ai_lock.locked(): return`。

---

## P1 — 高优先级（游戏质量/LLM 稳定性）

### P1-1 · `llm_strategy.py:100-104` — LLM raise amount 无上界
**文件**：`backend/src/ai/llm_strategy.py`
**问题**：`amount = max(min_raise, amount)` 只做下界，LLM 若返回超过玩家筹码的值，引擎拒绝 → 意外 fold。
**改动**：
```python
my_chips = me.get('chips', 0) + me.get('current_bet', 0)
amount = max(min_raise, min(amount, my_chips))
```

---

### P1-2 · `main.py:313-318` — AI Coach 无 LLM 时提示语硬编码中文
**文件**：`backend/src/main.py`
**问题**：英文用户收到中文提示。
**改动**：按 `_locale` 变量分支：
```python
if _locale == 'zh':
    body = '请先在 LLM 配置栏选择 AI 引擎。'
else:
    body = 'Select an AI engine in the LLM Config bar to use AI Coach.'
```

---

### P1-3 · `ollama.py:16` — Ollama 超时 30s 过长，无前端进度反馈
**文件**：`backend/src/ai/ollama.py`
**问题**：Bot 思考期间前端完全无响应，用户不知道是卡了还是在思考。
**改动**：
1. 将 `OLLAMA_TIMEOUT` 降至 `15.0`
2. `main.py` 在 LLM 调用前向前端 emit `ai_thinking` 事件（附 `player_id`），超时/完成后 emit `ai_thinking_done`
3. 前端 `PlayerBox` 展示转圈 loading indicator

---

### P1-4 · `coach.py:32` — JSON 正则过于宽松
**文件**：`backend/src/ai/coach.py`
**问题**：`r'\{.*\}'` (DOTALL) 匹配从第一个 `{` 到最后一个 `}`，LLM 后缀说明文字中若含括号则抓错。
**改动**：改为 `r'\{[^{}]*\}'` 或用逐字符 JSON 查找器。

---

### P1-5 · `engine.py:232-234` — raise 验证可读性极差
**文件**：`backend/src/engine.py`
**问题**：双重否定条件，极易误读（虽然逻辑最终正确）。
**改动**：提取为具名变量，提升可维护性：
```python
if amount < self.current_bet + self.min_raise:
    is_all_in_raise = (amount >= p.chips + p.current_bet)
    if not is_all_in_raise:
        raise ValueError(f"Raise too small. Min total: {self.current_bet + self.min_raise}")
```

---

## P2 — 中优先级（游戏体验提升）

### P2-1 · Bot 等待时间上限过长
**文件**：`backend/src/main.py`
**问题**：GRANITE (rock) 最慢 4.5s，GLACIER 最慢 4s，连续几手牌后玩家等待感极强。
**改动**：调整 `BOT_THINK_TIME`：
```python
'bot_2': (1.5, 3.0),   # GRANITE — 慢但不超过 3s
'bot_4': (1.2, 3.0),   # GLACIER — 同上
```

---

### P2-2 · Showdown 结果停留时间不足
**文件**：`frontend/src/store/useGameStore.ts` + `frontend/src/components/table/PokerTable.tsx`
**问题**：FINISHED 状态立刻可点击"下一手"，玩家来不及看结果。
**改动**：FINISHED 状态后 emit `showdown_result` 事件，前端延迟 2.5s 再显示"Next Hand"按钮。

---

### P2-3 · ActionBar Raise 输入缺乏上界视觉提示
**文件**：`frontend/src/components/layout/ActionBar.tsx`
**问题**：用户输入超额数字时只有点击后才报错，无即时反馈。
**改动**：输入值 > `maxRaise` 时 input border 变红并显示 `Max: {maxRaise}` 文字。

---

### P2-4 · Bot 聊天消息竞态清除
**文件**：`frontend/src/store/useGameStore.ts`
**问题**：两条相同内容的 chat 到达时，第一条的自动清除 timer 会误清除第二条。
**改动**：Timer 改为基于 `player_id + timestamp` 的 key，而非 chat 内容比较。

---

### P2-5 · AI Coach 建议请求 flag 未重置
**文件**：`frontend/src/store/useGameStore.ts`
**问题**：用户在 `isRequestingAdvice=true` 时关闭 Coach 面板，flag 永不重置，下次打开卡在 loading。
**改动**：Coach 面板 `onClose` 时强制 `set({ isRequestingAdvice: false })`。

---

### P2-6 · `equity.py` 蒙特卡洛模拟次数偏少
**文件**：`backend/src/ai/equity.py`
**问题**：300 次模拟有 ±5-10% 方差，GTO bot 决策质量抖动明显。
**改动**：提高至 500 次（对延迟影响极小，精度显著提升）。

---

## P3 — 低优先级（代码质量 / 长期维护）

### P3-1 · 删除废弃代码 `ai_service.py`
**文件**：`backend/src/ai_service.py`
**问题**：该文件是早期遗留，从未被 import，造成混淆。
**改动**：直接删除。

---

### P3-2 · 魔法数字提取为常量
**文件**：`backend/src/ai/rule_based.py`, `backend/src/ai/gto_strategy.py`
**问题**：40%/55% pot bluff sizing、0.20 equity threshold 等散落在代码各处。
**改动**：提取到各文件顶部的 `# ─── Constants` 区块。

---

### P3-3 · 补充测试用例
**文件**：`backend/tests/test_poker_logic.py`
**问题**：缺少对 `rule_based.py` 决策的测试、LLM 响应解析的测试（包括畸形 JSON、无效 action）。
**改动**：新增：
- `TestRuleBasedStrategy` — 覆盖 5 种 personality 在 weak/medium/strong 手牌下的决策分布
- `TestLLMResponseParsing` — 测试 malformed JSON、amount 超界、invalid action fallback

---

### P3-4 · Docker healthcheck 改用 curl
**文件**：`docker-compose.yml`
**问题**：`python3 -c "import urllib.request..."` 比直接 `curl` 慢约 300ms，且镜像未必有 python3 在 PATH。
**改动**：
```yaml
test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
```

---

### P3-5 · Socket.IO 断线重连加指数退避
**文件**：`frontend/src/store/useGameStore.ts`
**问题**：当前断线后立刻重连，网络不稳时可能连续轰炸服务器。
**改动**：Socket.IO 配置加 `reconnectionDelay: 1000, reconnectionDelayMax: 10000`。

---

## 执行顺序建议

```
Week 1:  P0-1 → P0-2 → P0-3 → P0-4   (引擎稳定性，必须先做)
Week 1:  P1-1 → P1-2 → P1-4 → P1-5   (LLM 和可读性)
Week 2:  P1-3 → P2-1 → P2-2 → P2-3   (体验提升)
Week 2:  P2-4 → P2-5 → P2-6           (细节打磨)
Week 3:  P3-1 → P3-2 → P3-3           (代码质量)
Week 3:  P3-4 → P3-5                   (基础设施)
```

---

## 每项改动完成后验收标准

- **P0 类**：运行 `pytest backend/tests/ -v`，全部通过；手动连续点击 5 次 action 不触发 `Not your turn` 报错
- **P1 类**：LLM bot 在 Qwen/Ollama 超时场景下自动 fallback，不 freeze
- **P2 类**：QA 人工测试 UI 交互流程
- **P3 类**：`pytest` + code review 通过即可

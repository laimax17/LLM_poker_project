# LLM 部署 Playbook — Cyber Hold'em

> 本文档面向需要配置或切换 AI 引擎的开发者和运维人员。
> 新成员按本文档操作，10 分钟内即可跑通 Ollama 或 Qwen 引擎。

---

## 架构总览

```
浏览器
  └─ Socket.IO / HTTP
        └─ FastAPI backend (main.py)
              └─ _build_strategy(engine, model)
                    ├─ "rule-based" → GTOBotStrategy              # 无需 LLM
                    ├─ "gto"        → GTOBotStrategy              # 无需 LLM
                    ├─ "ollama"     → OllamaClient                # 本地推理
                    └─ <provider>   → OpenAICompatibleClient      # 云端，统一客户端
                          （provider/模型清单见 ai/providers.py）
```

**统一客户端**：所有云端 provider（OpenRouter、DeepSeek、…）都走同一个
`OpenAICompatibleClient`，由 `base_url + api_key` 决定 provider、`model` 字符串决定模型。
新增 provider = 在 `ai/providers.py` 加一个 `ProviderSpec`；新增模型 = 加一行 `ModelSpec`。

**关键机制**：LLM 引擎仅在 **Flop / Turn / River** 调用模型决策；Pre-flop 始终由规则引擎处理以保证速度。
翻后会把预算好的胜率/底池赔率/位置/牌面质地 + 对手画像一起喂给模型（增强提示 + 对手记忆）。

---

## 引擎能力对比

| 引擎 | Bot 决策 | AI Coach | Key | 推荐场景 |
|------|----------|----------|-----|----------|
| `rule-based` | GTO + 人格 | GTO 计算型 | 无 | 本地调试 / 演示 |
| `gto` | 位置 + 蒙特卡洛 | GTO 计算型 | 无 | 无网络环境 |
| `ollama` | LLM agent（后街）| LLM 分析 | 无（本机推理）| 本地 + 数据隐私 |
| `openrouter` | LLM agent（后街）| LLM 分析 | `OPENROUTER_API_KEY` | 一个 key 用全部主流模型 |
| `deepseek` | LLM agent（后街）| LLM 分析 | `DEEPSEEK_API_KEY` | 成本最低、中文好 |

---

## 方式 A：本地 Ollama

### 前置要求

- 安装 [Ollama](https://ollama.ai)（支持 macOS / Linux / Windows WSL2）
- 硬件：推理 7B 模型建议 ≥ 16 GB RAM 或 8 GB VRAM

### Step 1 — 拉取模型

```bash
# 推荐：中文理解好，速度快
ollama pull qwen2.5:7b

# 备选（质量更高，但更慢）
ollama pull qwen2.5:14b
ollama pull llama3.1:8b

# 验证已下载
ollama list
```

### Step 2 — 启动 Ollama 服务

```bash
ollama serve
# 默认监听 http://localhost:11434

# 健康验证
curl http://localhost:11434/api/tags
```

### Step 3 — 配置环境变量

```bash
cp backend/.env.example backend/.env
```

```ini
# backend/.env
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b
DEFAULT_AI_ENGINE=ollama
```

> **Docker 用户**：容器内访问宿主机 Ollama，需改为：
> ```ini
> OLLAMA_HOST=http://host.docker.internal:11434
> ```
> `docker-compose.yml` 已配置 `extra_hosts: host.docker.internal:host-gateway`，开箱支持。

### Step 4 — 启动服务

```bash
# Ollama 跑在宿主机（推荐）
docker compose up -d

# Ollama 也跑在容器里（GPU 场景）
docker compose --profile with-ollama up -d
docker compose exec ollama ollama pull qwen2.5:7b
```

### Step 5 — 游戏内切换引擎

**方式一：UI 操作**

1. 打开 `http://localhost:3000`
2. 顶部 LLMConfigBar → Engine 选 `Ollama`
3. Model 填写与 Step 1 一致的模型名（如 `qwen2.5:7b`）
4. 点击 `Connect` → 状态指示灯变绿 `ONLINE`

**方式二：HTTP API**

```bash
curl -X POST http://localhost:8000/ai/config \
  -H 'Content-Type: application/json' \
  -d '{"engine": "ollama", "model": "qwen2.5:7b"}'
```

### Step 6 — 验证

```bash
curl http://localhost:8000/health
# 期望输出
# {"status":"ok","engine":"ollama","model":"qwen2.5:7b","llm_connected":true}
```

### 故障排查

| 现象 | 原因 | 解决方案 |
|------|------|----------|
| `llm_connected: false` | Ollama 未启动 | `ollama serve` |
| Bot 决策超时 | 模型过大或 CPU 推理 | 换 `qwen2.5:7b`，或降至 `3b` |
| `model "xxx" not found` | 模型名拼错或未 pull | `ollama list` 核查 |
| Docker 内 `Connection refused` | `OLLAMA_HOST` 错误 | 改为 `host.docker.internal:11434` |
| Bot 全部 fold | LLM 响应格式不符 | 查后端日志 `docker compose logs -f backend` |

---

## 方式 B：云端 provider（OpenRouter / DeepSeek，统一客户端）

所有云端 provider 共用同一个 OpenAI 兼容客户端。**每个 provider 只需一个 key**，
填在 `backend/.env` 里即可——未配置 key 的 provider 在 UI 中显示为 `NO KEY`。

### Step 1 — 申请 key

| Provider | 申请地址 | 特点 |
|----------|----------|------|
| OpenRouter | https://openrouter.ai/keys | 一个 key 直达 GPT / Claude / Gemini / DeepSeek / Qwen / Llama |
| DeepSeek | https://platform.deepseek.com | 直连，成本最低，中文强 |

### Step 2 — 配置 .env

```bash
cp backend/.env.example backend/.env
```

```ini
# backend/.env —— 填你拥有的 key（都可选填）
OPENROUTER_API_KEY=sk-or-xxxxxxxx
DEEPSEEK_API_KEY=sk-xxxxxxxx

# 启动默认引擎与模型（可选）
DEFAULT_AI_ENGINE=openrouter
LLM_MODEL=openai/gpt-4o-mini
```

> **安全**：`.env` 已在 `.gitignore`，严禁提交到 Git 仓库。

### Step 3 — 模型清单

模型清单维护在 `backend/src/ai/providers.py` 的 `MODELS`，前端通过
`GET /ai/models` 自动拉取并按 provider 分组。当前内置（节选）：

| Provider | 模型 ID | 说明 |
|----------|---------|------|
| openrouter | `openai/gpt-4o-mini` | 便宜快，默认 |
| openrouter | `anthropic/claude-3.5-sonnet` | 推理强 |
| openrouter | `deepseek/deepseek-chat` | 性价比高 |
| deepseek | `deepseek-chat` | 直连，最便宜 |
| deepseek | `deepseek-reasoner` | 带推理 |

新增模型只需在 `MODELS` 加一行 `ModelSpec(id, label, provider)`。

### Step 4 — 启动并验证

```bash
docker compose up -d

curl http://localhost:8000/health
# 期望：{"status":"ok","engine":"openrouter","llm_connected":true}

curl http://localhost:8000/ai/models   # 查看 provider 可用性 + 模型清单
```

### Step 5 — 游戏内切换

LLMConfigBar → Engine 选 `OPENROUTER` / `DEEPSEEK` → Model 选具体模型。

### 故障排查

| 现象 | 原因 | 解决方案 |
|------|------|----------|
| 引擎显示 `NO KEY` | 对应 `*_API_KEY` 未设置 | 在 `backend/.env` 填入 key 后重启 |
| `401 Unauthorized` | key 无效或含空格 | 重新复制 key |
| `llm_connected: false` | 网络/防火墙拦截 | 测试 `curl https://openrouter.ai` 连通性 |
| Bot 频繁 fold | JSON 解析失败 | 查日志确认 LLM 响应格式；换更强的模型 |

---

## 运行时动态切换引擎

无需重启服务，随时热切换：

```bash
# 切到 OpenRouter + Claude
curl -X POST http://localhost:8000/ai/config \
  -d '{"engine":"openrouter","model":"anthropic/claude-3.5-sonnet"}' \
  -H 'Content-Type: application/json'

# 切到 DeepSeek 直连
curl -X POST http://localhost:8000/ai/config \
  -d '{"engine":"deepseek","model":"deepseek-chat"}' \
  -H 'Content-Type: application/json'

# 切回纯规则（最快，无 API 消耗）
curl -X POST http://localhost:8000/ai/config \
  -d '{"engine":"rule-based","model":""}' \
  -H 'Content-Type: application/json'

# 切到本地 Ollama 并指定模型
curl -X POST http://localhost:8000/ai/config \
  -d '{"engine":"ollama","model":"qwen2.5:14b"}' \
  -H 'Content-Type: application/json'
```

---

## 后端日志快速排查

```bash
# 实时日志
docker compose logs -f backend

# 正常启动标志
#   OllamaClient initialised: url=http://... model=qwen2.5:7b
#   OpenAICompatibleClient initialised: model=... base_url=https://openrouter.ai/api/v1
#   LLMBotStrategy decision for bot_3: raise

# 异常信号
#   LLMBotStrategy LLM call failed for bot_2 (falling back to rule-based): ...
#   LLM API error (...): 401 ...
#   OllamaClient HTTP error: Connection refused
```

---

## 环境变量速查表

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama 服务地址 |
| `OLLAMA_MODEL` | `qwen2.5:7b` | Ollama 默认模型 |
| `OPENROUTER_API_KEY` | _(可选)_ | OpenRouter API Key（一个 key 多模型）|
| `DEEPSEEK_API_KEY` | _(可选)_ | DeepSeek API Key |
| `DEFAULT_AI_ENGINE` | `rule-based` | 服务启动时的默认引擎 |
| `LLM_MODEL` | _(空)_ | 启动默认云端模型（如 `openai/gpt-4o-mini`）|

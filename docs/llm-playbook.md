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
                    ├─ "rule-based" → RuleBasedStrategy     # 无需 LLM
                    ├─ "gto"        → GTOBotStrategy         # 无需 LLM
                    ├─ "ollama"     → OllamaClient           # 本地推理
                    ├─ "qwen-plus"  → QwenClient (DashScope) # 云端 API
                    └─ "qwen-max"   → QwenClient (DashScope) # 云端 API（更强）
```

**关键机制**：LLM 引擎仅在 **Flop / Turn / River** 调用模型决策；Pre-flop 始终由 RuleBasedStrategy 处理以保证速度。

---

## 引擎能力对比

| 引擎 | Bot 决策 | AI Coach | 需要网络 | 推荐场景 |
|------|----------|----------|----------|----------|
| `rule-based` | 5 种人格规则 | GTO 计算型 | 否 | 本地调试 / 演示 |
| `gto` | 位置 + 蒙特卡洛 | GTO 计算型 | 否 | 无网络环境 |
| `ollama` | LLM（后街）| LLM 分析 | 否（本机推理）| 本地 + 数据隐私 |
| `qwen-plus` | LLM（后街）| LLM 分析 | 是 | 生产推荐（速度/质量平衡）|
| `qwen-max` | LLM（后街）| LLM 分析 | 是 | 最强分析质量 |

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

## 方式 B：阿里云 DashScope（Qwen 云端）

### 前置要求

- 阿里云账号，开通 [DashScope](https://dashscope.console.aliyun.com) 服务
- 获取 API Key：控制台 → API-KEY 管理 → 创建

### Step 1 — 配置 API Key

```bash
cp backend/.env.example backend/.env
```

```ini
# backend/.env
DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
QWEN_MODEL=qwen-plus
DEFAULT_AI_ENGINE=qwen-plus
```

> **安全**：`.env` 已在 `.gitignore`，严禁提交到 Git 仓库。

### Step 2 — 模型选型

| 模型 ID | 引擎名 | 响应延迟 | 推理质量 | 参考费用 |
|---------|--------|----------|----------|----------|
| `qwen-turbo` | 自定义填写 | ~1s | 基础 | 最低 |
| `qwen-plus` | `qwen-plus` | ~2s | 中等 | 低 |
| `qwen-max` | `qwen-max` | ~4s | 最强 | 中 |

推荐生产环境使用 **`qwen-plus`**，在速度和质量之间取得最佳平衡。

### Step 3 — 启动并验证

```bash
docker compose up -d

curl http://localhost:8000/health
# 期望：{"status":"ok","engine":"qwen-plus","llm_connected":true}
```

### Step 4 — 游戏内切换

LLMConfigBar → Engine 选 `Qwen Plus` 或 `Qwen Max` → 点击 `Connect`

### 故障排查

| 现象 | 原因 | 解决方案 |
|------|------|----------|
| `401 Unauthorized` | API Key 无效或含空格 | 检查 `.env` 文件，重新复制 Key |
| `llm_connected: false` | 网络/防火墙拦截 | `curl https://dashscope.aliyuncs.com` 测试连通性 |
| Bot 频繁 fold | JSON 解析失败 | 查日志确认 LLM 响应格式；尝试换 `qwen-max` |
| 费用异常 | health_check 调用次数多 | 游戏结束后关闭浏览器 Tab 停止轮询 |

---

## 运行时动态切换引擎

无需重启服务，随时热切换：

```bash
# 切到 Qwen Max
curl -X POST http://localhost:8000/ai/config \
  -d '{"engine":"qwen-max","model":"qwen-max"}' \
  -H 'Content-Type: application/json'

# 切回纯规则（最快，无 API 消耗）
curl -X POST http://localhost:8000/ai/config \
  -d '{"engine":"rule-based","model":""}' \
  -H 'Content-Type: application/json'

# 切到 GTO 模式
curl -X POST http://localhost:8000/ai/config \
  -d '{"engine":"gto","model":""}' \
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
#   QwenClient initialised: model=qwen-plus
#   LLMBotStrategy decision for bot_3: raise

# 异常信号
#   LLMBotStrategy LLM call failed for bot_2 (falling back to rule-based): ...
#   QwenClient API error: 401 ...
#   OllamaClient HTTP error: Connection refused
```

---

## 环境变量速查表

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama 服务地址 |
| `OLLAMA_MODEL` | `qwen2.5:7b` | Ollama 默认模型 |
| `DASHSCOPE_API_KEY` | _(必填)_ | 阿里云 DashScope API Key |
| `QWEN_MODEL` | `qwen-plus` | Qwen 云端默认模型 |
| `DEFAULT_AI_ENGINE` | `rule-based` | 服务启动时的默认引擎 |

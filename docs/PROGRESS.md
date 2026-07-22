# 进度跟踪 — Second Brain Agent

> 按 PLAN.md 的 P0-P9 阶段跟踪实现状态。最新更新：2026-07-06

## 项目定位

**个人/团队的 Second Brain（第二大脑）**：
- 把散落的文章、对话、笔记、图片统一塞进一个可检索的知识库
- 通过对话提问，让 LLM 基于知识库内容给出有引用的回答
- 多 LLM 切换（OpenAI / Anthropic / Deepseek / 智谱 / 月之暗面 / Ollama / 自定义）
- 每个会话独立持久化，可回顾历史

## 技术栈

| 层 | 技术 | 说明 |
|---|---|---|
| **后端框架** | FastAPI 0.115+ | 异步 REST + SSE 流式 |
| **LLM 编排** | LangGraph 0.2+（按设计不用 LangChain 全家桶） | `retrieve → answer` 两节点图 |
| **LLM 接口** | `langchain-openai` + `init_chat_model` | 通过 `base_url` 路由多 provider |
| **Embedding** | OpenAI `text-embedding-3-small` | 通过工厂切换 base_url |
| **向量库** | ChromaDB 0.5+ | 本地持久化到 `data/chroma/` |
| **关系库** | SQLite + SQLModel | `notes.db` + FTS5 全文索引 |
| **Web 爬虫** | trafilatura 1.12+ | URL 入库用 |
| **PDF 解析** | pypdf 5.0+ | 多页文本抽取 |
| **HTTP 客户端** | httpx 0.27+ | 调上游 `/v1/models` + LLM |
| **配置** | pydantic-settings + python-dotenv | `.env` 加载 |
| **前端框架** | Vue 3.5 + Vite 6 + TypeScript | `<script setup>` + SFC |
| **状态管理** | Pinia 3 | chat / settings / sessions / notes / models 五个 store |
| **UI 库** | Naive UI 2.41 | 暗色主题 |
| **路由** | vue-router 4 | createWebHistory（path 模式）|
| **SSE 解析** | 自写 `streamSse` | `fetch` + `ReadableStream` |
| **构建** | pnpm 11.5 + Vite HMR | 开发体验 |

## 已实现功能

### ✅ F1 多 LLM 切换 + Auto 模式
- 后端 `factory.py` 路由 7 家 provider：
  - OpenAI / Anthropic（langchain 原生）
  - Deepseek / 智谱 / 月之暗面 / SiliconFlow / Ollama（OpenAI 兼容 + `base_url`）
- `Auto` 模式：选定后不传 provider/model，走 `.env` 默认
- 用户 key 走 `X-API-Key` header，优先级 `header > body.api_key > .env`
- 每个请求可临时覆盖 `base_url` / `api_key` / `provider` / `model` / `reasoning_level`

### ✅ F2 自动识别模型清单
- 后端 `POST /api/settings/custom-models`：httpx 调 `<base_url>/models`，Bearer 鉴权
- 自动推断 provider（按 URL 关键字：deepseek / zhipu / moonshot / siliconflow / ollama / openai）
- 设置页表单 → 一键识别 → 列表展示 → 入库

### ✅ F3 推理程度选择（4 档）
- 每个模型独立存 `reasoning: low | medium | high | xhigh`，localStorage 持久化
- 选中模型后旁边出现 80px 紧凑下拉
- 后端映射：OpenAI o-series 走 `reasoning_effort`；其它 provider 当前忽略

### ✅ F4 RAG 检索（向量 + 关键词混合）
- `storage/hybrid.py`：向量 0.7 + FTS5 关键词 0.3 加权融合
- 去重按 `note_id+chunk_index`
- `top_k=5`，按分数排序

### ✅ F5 引用卡片
- 答案每条事实后强制 `[n]` 标注
- 流式推送 `event: citations` → 前端 `CitationCard.vue` 展示
- 显示：编号 / 来源标题 / chunk_index / score / snippet

### ✅ F6 入库链路
- URL → `fetch_url` (trafilatura) → 切块 → embedding → 入 Chroma + SQLite
- 文本 → `ingest_text` → 同上
- PDF 上传 → pypdf 抽文本 → 同上

### ✅ F7 对话持久化（每会话独立）
- `ChatSession` + `ChatMessage` 表
- 标题自动从首条 user 消息截前 50 字
- 不带 `session_id` 时后端自动创建会话并通过 SSE `event: session` 推送
- 侧栏立即刷新（不等流结束）

### ✅ F8 SSE 流式回答
- `event: session` → `event: citations` → `data: 文字片段`（8 字符 chunks） → `data: [DONE]`
- 前端 `streamSse` 异步生成器逐 token 渲染

### ✅ F9 用户隔离的 API Key
- 浏览器 `localStorage` → `X-API-Key` header
- 不上传服务端，每次请求自动带
- 设置页可「保存 / 清除」

### ✅ F10 体验打磨（部分）
- 暗色主题统一
- 会话侧栏：标题 + 预览 + 时间 + 消息数 + × 删除
- 模型选择下拉：避免被压窄（`min-width: 220px` + menu-props）
- 输入框聚焦不抢眼（自定义 CSS）
- RAG switch 独立开关

---

## 阶段完成度（按 PLAN.md）

| 阶段 | 内容 | 状态 |
|---|---|---|
| **P0** | 计划书 | ✅ |
| **P1** | 后端骨架 | ✅ |
| **P2** | 入库链路 | ✅ |
| **P3** | 检索 + 问答 | ✅ |
| **P4** | Agent 化（intent_router 路由）| 🟡 仅 retrieve→answer |
| **P5** | 前端骨架 | ✅ |
| **P6** | 端到端联调 | ✅ |
| **P7** | 多模型切换 | ✅ + Auto + 自定义 base_url |
| **P8** | 体验打磨 | 🟡 部分（loading / 错误态 / 响应式 待补）|
| **P9** | 高级（OCR / RSS / 周报 / MCP）| ❌ 未开始 |

---

## 本轮新增（v0.4 — 多 LLM + 知识库雏形）

### 设计决策
1. **不用 LangChain 全家桶**：`init_chat_model` + 自定义 `get_llm(api_key, base_url, reasoning)` 更灵活
2. **多 provider 用 OpenAI 兼容路由**：用 `langchain-openai` 的 `model_provider="openai" + base_url` 覆盖 5 家
3. **localStorage 存自定义 LLM**：跨刷新、跨 tab 同步，每次进聊天页都从 storage.load() 启动
4. **reasoning per-model**：每个模型独立存推理程度，选不同模型自动切
5. **侧栏边输入边入 list**：SSE 收 `session` 事件就调 `sessions.load()`，不等流结束

### 文件改动
| 文件 | 改动 |
|---|---|
| `backend/app/llm/factory.py` | 加 `base_url` / `reasoning_level` 参数；`_REASONING_MAP` 翻译 |
| `backend/app/api/settings.py` | 加 `POST /settings/custom-models` |
| `backend/app/api/chat.py` | 加 `base_url / api_key / reasoning_level` 字段；优先级链 |
| `backend/app/agent/state.py` + `answer.py` | 透传新覆盖字段 |
| `frontend/src/stores/models.ts` | **新建** 自定义 LLM 持久化 |
| `frontend/src/api/custom-models.ts` | **新建** detectModels API |
| `frontend/src/components/ModelSelector.vue` | 重写：单 select + 推理下拉（仅选中时显示）|
| `frontend/src/components/ChatHistory.vue` | 删小字，empty 文案优化 |
| `frontend/src/views/ChatView.vue` | 重排：输入框大，模型选择下 |
| `frontend/src/views/SettingsView.vue` | 重写：自定义 LLM 表单 |
| `frontend/src/App.vue` | `router-link` 替换 anchor（修复 hash 不触发路由）|
| `frontend/src/style.css` | 抑制 n-input 聚焦边框高亮 |
| `frontend/src/stores/chat.ts` | 流中收到 `session` 立即 `sessions.load()` |

---

## 待办 / 下一阶段

### P8 体验打磨
- [ ] 入库流式进度（chunk 级别）
- [ ] 移动端响应式 / drawer 侧栏
- [ ] 全局错误边界
- [ ] 笔记详情页（含 chunk 视图 + 删除/重 embed）

### P9 高级
- [ ] **知识库 UI**（侧栏 📚 按钮 → 入库向导）
  - [ ] 图片 OCR（pytesseract + Pillow）
  - [ ] DOCX / Markdown / TXT 入库
  - [ ] 拖拽上传
  - [ ] 入库批次 + 进度
- [ ] RSS 定时抓取
- [ ] 周报 / 知识图谱
- [ ] MCP server 暴露知识库给其它 agent

### 期望先做的具体项（按用户最近 ask）
1. **📚 知识库按钮** 放进侧栏（`ChatHistory.vue`），跳转 `/notes`
2. **图片上传 + OCR** 后端 `/notes/image` 端点 → pytesseract；前端拖拽 / 点击上传
3. **多格式入库**：DOCX / Markdown / TXT

---

## 验证记录

| 日期 | 测试 | 结果 |
|---|---|---|
| 2026-07-06 | 后端启动 + 13 路由 | ✅ |
| 2026-07-06 | `POST /settings/custom-models` | ✅（401/200 已测）|
| 2026-07-06 | LLM 7 provider factory | ✅ |
| 2026-07-06 | FTS5 + Chroma 混合检索 | ✅ |
| 2026-07-06 | SSE 流 + citations | ✅ |
| 2026-07-06 | 用户 X-API-Key 覆盖 .env | ✅ |
| 2026-07-06 | 自定义 base_url + reasoning 透传 | ✅ |
| 2026-07-06 | `Ctrl+Shift+R` 触发 HMR 后清缓存 | 用户操作 |

---

## 完整文件清单

### 后端（`backend/app/`）
```
main.py                FastAPI 入口 + middleware
config.py              pydantic-settings
llm/factory.py         ★ 7 provider + reasoning + base_url override
embeddings/factory.py  OpenAI + 自定义 base_url
agent/
├── state.py           AgentState（messages, chunks, override 字段）
├── graph.py           LangGraph StateGraph（retrieve → answer）
└── nodes/
    ├── retrieve.py    hybrid_search
    └── answer.py      ANSWER_PROMPT + citations 收集
storage/
├── db.py              SQLite + SQLModel + FTS5 + ChatSession/ChatMessage
├── vector.py          Chroma collection 封装
└── hybrid.py          向量 0.7 + FTS5 0.3 加权
tools/
├── chunk.py           字符切块
├── fetch_url.py       trafilatura 抽正文
├── parse_pdf.py       pypdf
└── ingest.py          编排入口
api/
├── health.py
├── chat.py            SSE + RAG + session 创建 + override 透传
├── search.py
├── notes.py           URL / text / pdf 入库
└── settings.py        models + custom-models
```

### 前端（`frontend/src/`）
```
main.ts / App.vue / style.css
router/index.ts              createWebHistory
api/
├── client.ts                fetch + X-API-Key + streamSse
├── chat.ts                  SSE 解析 + citations
├── notes.ts
├── settings.ts
└── custom-models.ts         detectModels
stores/
├── chat.ts                  session 立即入 list
├── sessions.ts              CRUD
├── notes.ts
├── settings.ts              apiKey state
└── models.ts                ★ 自定义 LLM + 推理程度
components/
├── ChatHistory.vue          侧栏（+ 知识库 + 列表）
├── MessageBubble.vue
├── ModelSelector.vue        ★ Auto + 独立推理下拉
├── CitationCard.vue
└── NotesView（已存在，待增强）
views/
├── ChatView.vue             ★ 输入框大、模型选择下
├── NotesView.vue            待重写为入库存放 + OCR
└── SettingsView.vue         ★ 自定义 LLM 表单
```

---

## v0.5 — PydanticAI migration (2026-07-06)

**Motivation**: remove langchain/langgraph dependencies in favor of PydanticAI for type-safe structured output and less ceremony.

### Changes
- `requirements.txt`: removed `langchain*`, `langgraph*`; added `pydantic-ai[openai,anthropic]>=0.2`
- `app/agent/schemas.py` (new): `AnswerResult`, `Citation`, `Deps` Pydantic models
- `app/llm/factory.py`: `get_llm()` (LangChain) → `get_agent()` (PydanticAI)
- `app/agent/nodes/answer.py`: `init_chat_model().invoke()` → `Agent(output_type=AnswerResult).run_sync()`
- `app/api/chat.py`: uses `answer_node_stream()` async generator
- `app/agent/graph.py`: deleted (LangGraph was never wired in)
- Embeddings factory already on httpx (no openai SDK) — unchanged
- Frontend: unchanged (API contract preserved)

### Uninstalled packages
```
pip uninstall -y langchain langchain-core langchain-openai langchain-anthropic \
  langchain-protocol langgraph langgraph-checkpoint langgraph-prebuilt langgraph-sdk
```

### Migration map
| LangChain | PydanticAI |
|---|---|
| `init_chat_model(model, model_provider=..., base_url=...)` | `OpenAIChatModel(model_name, provider=OpenAIProvider(base_url=..., api_key=...))` |
| `llm.invoke(prompt).content` | `agent.run_sync(query).output.text` |
| manually-typed tool defs | `@agent.tool` (Pydantic schema auto-derived) |
| manual JSON parsing for citations | `output_type=AnswerResult` → `result.output.citations` |
| `StateGraph` orchestration | `agent.iter()` / direct call (linear flow) |

### Verified
- All 13 backend files pass AST check
- FastAPI app boots (10 routes registered)
- Factory smoke test: 5 provider variants (openai, custom base_url, o1-mini+reasoning, anthropic, deepseek native) all create models
- `/api/health` and `/api/settings/models` return 200
- Zero `langchain` / `langgraph` references remain in `app/` code

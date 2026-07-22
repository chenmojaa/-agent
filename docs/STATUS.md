# HD 个人知识库 — 当前状态 (2026-07-22)

HD = 个人知识库 + 多 LLM + RAG + Skill 推荐。

## 技术栈
- 后端：FastAPI + LangChain 1.3 + LangGraph 1.2 + Pydantic v2 + SQLite (FTS5) + Chroma
- 前端：Vue 3 + Vite + naive-ui + Pinia
- 端口 8001（uvicorn）, 5173（vite dev）
- LLM / Embedding：OpenAI / MiniMax / 其他 OpenAI-compatible `/v1/chat`、`/v1/embeddings`
- OCR：Tesseract（`chi_sim` 需单独装）

## 目录结构
- backend/
  - app/main.py · FastAPI 入口
  - app/api/ · REST 路由 (chat / notes / search / sessions / settings / health)
  - app/agent/ · LangGraph (graph.py + nodes/retrieve.py + nodes/answer.py)
  - app/embeddings/factory.py · 唯一 embedding 客户端（OpenAI-compatible + MiniMax 原生 body）
  - app/storage/vector.py · Chroma wrapper + FTS5 sync
  - app/storage/db.py · SQLModel (Note/ChatSession/ChatMessage + chunk_fts 虚拟表)
  - app/storage/hybrid.py · 向量 + 关键词混合检索
  - app/tools/ingest.py · 11 个 ingest 函数 (pdf/docx/pptx/xlsx/csv/html/txt/image/url/text/file)
  - app/tools/ocr.py · Tesseract 包装
- frontend/
  - src/api/ · 后端 HTTP 客户端
  - src/stores/ · Pinia stores (chat / notes / sessions / models / settings)
  - src/views/ · 页面 (ChatView / NotesView / SettingsView)
  - src/components/ · 组件 (ChatHistory / MessageBubble / CitationCard / ModelSelector)
  - src/style.css · 全局 CSS 变量（light + dark + 蓝色 brand）

## 数据流
用户上传文件 -> NotesView -> api/notes.ts -> 后端 ingest_pdf/_docx/_image...
                       -> parse to .md
                       -> chunk_text（500/80）
                       -> embed_texts -> Chroma add_chunks + FTS5 add_fts
                       -> SQLite notes.{embedded=true, chunk_count=N}

用户发消息 -> ChatView -> chat.send()
                       -> store/chat.send()
                       -> chatStream() (api/chat.ts)
                       -> POST /chat (SSE)
                       -> backend api/chat.py:
                            use_rag=true:
                              hybrid_search(query, top_k=5, embedding_model, embedding_base_url, api_key)
                                -> embed_texts(query) [OPEN AI comp.]
                                -> vector_search(emb, top_k=10) [Chroma cosine]
                                -> fts_search(query, top_k=10) [SQLite FTS5 BM25]
                                -> merge + dedupe by (note_id, chunk_index)
                                -> score = 0.7 * vec + 0.3 * kw
                                -> trim top_k
                            -> graph.stream(initial_state)
                            -> graph:  retrieve → answer  (LangGraph)
                            -> answer_node: build_prompt(messages + chunks) -> LLM
                            -> SSE: session -> delta[*N] -> citations -> done
                            -> store: stream 累加 + stripThink + 渲染

## RAG 三层链路（必须三层都 OK）

| 层 | 文件 | 状态 | 说明 |
|---|---|---|---|
| 1. 入库 | api/notes.py + storage/vector.py + storage/db.py | OK | 笔记"无标题 CSV 506 chunks"验证通过 |
| 2. 检索 | api/chat.py hybrid_search + api/search.py | OK（缺真实 key 即时） | call: hybrid_search(query, top_k, api_key, base_url, model) |
| 3. prompt | agent/nodes/answer.py | OK | chunks → system prompt "请基于以下参考回答" |

**关键约束（修复要点）**：
- 前端默认 use_rag=true (stores/chat.ts:22, stores/chat.ts:52 传 use_rag: this.useRag)
- 后端 hybrid_search 优先用 (api_key, base_url, model) 三个入参；为空时 fall back 到 settings.env/.env
- 前端 stores/chat.ts send() 读 useModelsStore().selected 拿到 embedding_model 并连同 base_url 传过去
- 前端默认 useModelsStore().selected??null（如果用户没在 settings 里加模型）
  -> 全空 -> 后端退到 .env 占位 -> 401 -> retrieved_chunks 空 -> LLM 不知道有 KB

## 主题颜色：HD 蓝
naive-ui 默认 primary 是绿色，已通过 n-config-provider themeOverrides 强制改为蓝色：

  primaryColor:       #3b82f6
  primaryColorHover:  #60a5fa
  primaryColorPressed: #2563eb
  infoColor:          #3b82f6
  successColor:       #3b82f6   <- 即使遗留 type="success" 也是蓝

App.vue 用 <n-config-provider :theme="naiveTheme" :theme-overrides="naiveOverrides">。

## 大小写 / 文件写入约定（PowerShell UTF-8 无 BOM）
参考 docs/file-writing-policy.md。文件落到 disk 必须用：

    [System.Text.UTF8Encoding]::new($false)

否则 Vue / Python parser 都会因为 BOM 字符报 invalid character / invalid token。

## 当前端点
| 方法 | 路由 | 用途 |
|---|---|---|
| GET | /api/health | 健康检查 |
| POST | /api/chat | SSE 聊天（含 RAG） |
| GET | /api/sessions | 会话列表 |
| POST | /api/sessions | 新建会话 |
| GET | /api/sessions/{id} | 会话详情 |
| DELETE | /api/sessions/{id} | 删会话 |
| POST | /api/search | 独立 hybrid 搜索（无需 LLM） |
| GET / POST / DELETE | /api/notes | CRUD 笔记 |
| POST | /api/notes/file | 文件上传入库 |
| POST | /api/notes/image | 图片 OCR 入库 |
| POST | /api/notes/text | 文本入库 |
| POST | /api/notes/url | URL 抓取入库 |
| POST | /api/notes/{id}/download | 下载磁盘 .md |
| POST | /api/notes/{id}/reembed | 重新跑 embedding |
| GET | /api/notes-stats | 笔记 + Chroma 计数 |

## 启动
```powershell
# backend
cd D:\one_agent\backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8001

# frontend (new shell)
cd D:\one_agent\frontend
npm run dev
```

## 用户使用流程
1. 设置 -> 添加自定义模型：填 base_url (e.g. https://api.minimax.chat/v1)、api_key
   -> 自动识别模型列表（识别期间 detach 请求 model list 拿到 model 名称）
   -> 勾选默认 + 手动填 embedding_model（如 embo-01 for MiniMax）
   -> 保存
2. 知识库 -> 上传 PDF/Word/图片/文本/URL
   -> 后端走 ingest_* 自动 chunk + embed + 存 Chroma + FTS5
   -> 状态从"未 embedding" 变成 "N chunks"
3. 聊天页：
   -> 输入框上方 NSwitch = 知识库 (开/关)
   -> 输入框旁边 ModelSelector (推理等级 + 模型名)
   -> 输入消息回车 -> 后端 SSE 流回
   -> 若知识库开启且 selected 模型有有效 key -> hybrid_search
   -> LLM prompt 包含 chunks -> 引用在 bubble 下方

---

## v0.7 -- RAG 链路完整贯通 (2026-07-22)

### 本轮修复（4 处代码改动，让 RAG 真正生效）

| 文件 | 原状 | 修复 |
|---|---|---|
| backend/app/api/chat.py `ChatRequest` | 只接受 9 个字段；前端发的 `embedding_*` 被 Pydantic 静默丢弃 | 增加 `embedding_model: str | None = None` 和 `embedding_base_url: str | None = None` |
| frontend/src/api/chat.ts `chatStream` | fetch body 只有 8 个字段 | 增加 `embedding_model` / `embedding_base_url`（从 `req` 透传）|
| backend/app/llm/factory.py `_build_model` | `model_kwargs={"reasoning_effort":...}`（新版已弃用，警告）| 改 `extra_body={"reasoning_effort":...}` |
| backend/app/storage/hybrid.py | `except Exception: pass` 两处吞错 | 加 `import logging`，错误改 `logging.warning(...)` 露出来 |

### 为什么修复前 RAG 完全不工作
- 前端 stores/chat.ts:send() 已经在 store 里准备好 embedding_model / embedding_base_url
- 前端类型 api/chat.ts:ChatRequest 已经声明这两个字段
- 但是 streamSse("/chat", {...}) body 里只塞了 8 个字段 → 后端永远收不到
- 同时后端 ChatRequest 也没有声明，即便前端真发了 Pydantic 也静默丢弃
- 后果：hybrid_search 退到 .env 占位 key → MiniMax 401 → except:pass → 引用列表永远空

### 后端验证（无需浏览器）

cd D:\one_agent\backend

$.venv\Scripts\python.exe -c "from app.storage.hybrid import hybrid_search; print(hybrid_search(query, top_k=3, base_url=url, api_key=key, model=emb_model))"

把 query=文化和旅游厅 / url=https://api.minimax.chat/v1 / key=你的真 key / emb_model=embo-01 代进去。
成功后命中：note_id=n_ed3e8c176608 chunk_index=86 kw_score=0.166 ✅

### 浏览器侧如何启用
1. 设置 → 添加自定义模型 entry：baseUrl=https://api.minimax.chat/v1，apiKey=真 key，embeddingModel=embo-01
2. 保存
3. 知识库 — 已有 笔记「无标题」506 chunks + 「介绍」2 chunks
4. 聊天页 → 顶部 知识库 开关打开 → 发问
5. 看 LLM 答案下面的 CitationCard

### 给下一位 LLM 的速查
- 用户 Chrome Network 里 /api/chat body 没 embedding_model → F5 或 Ctrl+Shift+R 强刷前端，TS 已经发了，只是浏览器缓存旧 JS。
- Chroma count()=0 → 看 backend/uvicorn.err.log 的 hybrid_search embed failed 真实报错（已不再静默）。
- embedded=False → 设置页加模型后，用笔记列表旁的「重跑 embedding」按钮触发重新入库。

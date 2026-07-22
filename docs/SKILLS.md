# Skill 中心 — 当前实现

侧栏 -> `Skill` 按钮 -> 弹三个 Tab。

## 数据源（前端常量）
`frontend/src/components/ChatHistory.vue` 中 `FEATURED` 数组：

| id | name | emoji | category | badge |
|---|---|---|---|---|
| web-search | Web Search | 馃攷 | research | 热推 |
| code-review | Code Review | 馃И | dev | 热门 |
| doc-summarizer | Doc Summarizer | 馃摑 | productivity | 编辑推荐 |
| sql-coach | SQL Coach | 馃梼锔?/td> | dev | |
| travel-planner | Travel Planner | 馃С | life | |
| translator | Bilingual 译员 | 馃寪 | productivity | |
| image-prompt | Image Prompt | 馃帹 | creative | |
| math-tutor | Math Tutor | 鈭?/td> | study | |

## 三个 Tab 行为
1. **推荐首页**：渲染 `FEATURED` 前 5 条；右上角"一键导入推荐"全部加入本地 `installed` map
2. **查看更多**：渲染所有 8 条；分类 tag 显示
3. **我的 Skill**：列出 `installed` 的 id

## 本地状态
- `installed: ref<Record<string, true>>` 仅 UI 状态
- 没有后端 / 没有持久化（关掉浏览器后丢）
- 单击卡片"导入"按钮 toggle

## 扩展（需后端配合时）：
- 在 `app/api/skills.py` 加路由：
  - GET /skills/featured -> 后端从 curated list 返回（10 条）
  - POST /skills/install {"skill_id": "web-search"} -> 写 sqlite
  - GET /skills/mine -> 查已安装的
- 现在前端 fetch 用 mock，store 加 loadFeatured() / install() action
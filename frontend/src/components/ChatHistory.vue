<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useSessionsStore } from '@/stores/sessions'
import { useChatStore } from '@/stores/chat'
import { NButton, NPopconfirm, NEmpty, NSpin, NText, NModal, NCard, NSpace, NInput, NTag } from 'naive-ui'

const sessions = useSessionsStore()
const chat = useChatStore()
const route = useRoute()
const router = useRouter()

const activeId = computed(() => (route.params.id as string) || null)

async function newChat() {
  chat.clear()
  router.push({ name: 'chat' })
}

function gotoNotes() {
  router.push({ name: 'notes' })
}

async function openSession(id: string) {
  if (id === activeId.value) return
  router.push({ name: 'chat-id', params: { id } })
}

async function removeSession(id: string, e: Event) {
  e.stopPropagation()
  await sessions.remove(id)
  if (activeId.value === id) {
    chat.clear()
    router.push({ name: 'chat' })
  }
}

function fmt(s: string) {
  try { return new Date(s).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }) }
  catch { return s }
}

// === Search dialog ===
const searchOpen = ref(false)
const searchQuery = ref("")
const searchedSessions = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return sessions.items
  return sessions.items.filter((s: any) => {
    const title = (s.title || "").toLowerCase()
    const preview = (s.preview || "").toLowerCase()
    return title.includes(q) || preview.includes(q)
  })
})

function openSearch() { searchQuery.value = ""; searchOpen.value = true }
function pickSession(id: string) { searchOpen.value = false; router.push({ name: "chat-id", params: { id } }) }

// === Skill dialog ===
const skillOpen = ref(false)
const skillTab = ref<"featured" | "all" | "mine">("featured")

interface SkillDef { id: string; name: string; emoji: string; desc: string; category: string; badge?: string }

const FEATURED: SkillDef[] = [
  { id: "web-search",     name: "Web Search",     emoji: "🔎", desc: "联网搜索、来源直达",         category: "research",     badge: "热推" },
  { id: "code-review",    name: "Code Review",    emoji: "🧪", desc: "解读 diff 提出改进建议",     category: "dev",          badge: "热门" },
  { id: "doc-summarizer", name: "Doc Summarizer", emoji: "📝", desc: "长文要点 + 三段式摘要",      category: "productivity", badge: "编辑推荐" },
  { id: "sql-coach",      name: "SQL Coach",      emoji: "🗃️", desc: "自然语言转 SQL 解释",        category: "dev" },
  { id: "travel-planner", name: "Travel Planner", emoji: "🧳", desc: "行程 / 票务 / 路线",        category: "life" },
  { id: "translator",     name: "Bilingual 译员",  emoji: "🌐", desc: "中英双向 + 风格选择",       category: "productivity" },
  { id: "image-prompt",   name: "Image Prompt",   emoji: "🎨", desc: "文字 → DALL·E/MJ 提示词",  category: "creative" },
  { id: "math-tutor",     name: "Math Tutor",     emoji: "∑",  desc: "中学到竞赛级逐步讲解",     category: "study" },
]

const installed = ref<Record<string, true>>({})
const featuredSkills = computed(() => FEATURED.slice(0, 5))
const allSkills = computed(() => FEATURED)

function openSkill() { skillOpen.value = true; skillTab.value = "featured" }
function toggleInstall(s: SkillDef) {
  if (installed.value[s.id]) delete installed.value[s.id]
  else installed.value[s.id] = true
}
function installAll(featured: SkillDef[]) { for (const s of featured) installed.value[s.id] = true }
</script>

<template>
  <div class="chat-history">
    <div class="chat-history-actions">
      <n-button block @click="newChat" class="action-btn new-chat-btn">+ 新对话</n-button>
      <n-button block quaternary @click="gotoNotes" class="action-btn">知识库</n-button>
      <n-button block quaternary @click="openSearch" class="action-btn">搜索对话</n-button>
      <n-button block quaternary @click="openSkill" class="action-btn">Skill</n-button>
    </div>
    <div class="chat-history-header">
      <span class="title">历史记录</span>
    </div>
    <div class="chat-history-list">
      <div v-if="sessions.loading && sessions.items.length === 0" class="loading-row">
        <n-spin size="small" />
        <n-text depth="3" style="font-size: 12px">加载中…</n-text>
      </div>
      <n-empty v-else-if="sessions.items.length === 0" size="small" description="点击 + 新对话 开始" style="padding: 24px 0" />
      <div
        v-for="s in sessions.items"
        :key="s.id"
        @click="openSession(s.id)"
        :class="['session-item', s.id === activeId ? 'active' : '']"
      >
        <div class="session-row">
          <span class="session-title">{{ s.title }}</span>
          <n-popconfirm @positive-click="removeSession(s.id, $event)">
            <template #trigger>
              <n-button text size="small" type="error" @click.stop class="delete-btn">✕</n-button>
            </template>
            删除该对话？
          </n-popconfirm>
        </div>
        <div v-if="s.preview" class="session-preview">{{ s.preview }}</div>
        <div class="session-meta">{{ fmt(s.updated_at) }} · {{ s.message_count }} 条</div>
      </div>
    </div>
  </div>
  <!-- 搜索对话 -->
  <n-modal v-model:show="searchOpen" preset="card" title="搜索对话" style="max-width: 480px">
    <n-input v-model:value="searchQuery" placeholder="搜索会话标题或预览片段" clearable />
    <n-space vertical size="small" style="margin-top: 12px; max-height: 360px; overflow-y: auto">
      <n-empty v-if="!sessions.loading && searchedSessions.length === 0" description="没有匹配的对话" />
      <div
        v-for="s in searchedSessions"
        :key="s.id"
        @click="pickSession(s.id)"
        class="search-item"
      >
        <div class="search-title">{{ s.title }}</div>
        <div v-if="s.preview" class="search-preview">{{ s.preview }}</div>
        <div class="search-meta">{{ fmt(s.updated_at) }} · {{ s.message_count }} 条</div>
      </div>
    </n-space>
  </n-modal>

  <!-- Skill 弹窗 -->
  <n-modal v-model:show="skillOpen" preset="card" title="Skill 中心" style="max-width: 760px">
    <n-space align="center" justify="space-between" style="margin-bottom: 12px">
      <n-space>
        <n-button :type="skillTab === 'featured' ? 'primary' : 'default'" size="small" @click="skillTab = 'featured'">推荐首页</n-button>
        <n-button :type="skillTab === 'all' ? 'primary' : 'default'" size="small" @click="skillTab = 'all'">查看更多</n-button>
        <n-button :type="skillTab === 'mine' ? 'primary' : 'default'" size="small" @click="skillTab = 'mine'">我的 Skill</n-button>
      </n-space>
      <n-button v-if="skillTab === 'featured'" size="small" type="primary" @click="installAll(featuredSkills)">一键导入推荐</n-button>
    </n-space>

    <n-space v-if="skillTab === 'featured'" vertical size="medium">
      <n-text depth="3" style="font-size: 12px">编辑精选 · 适合 HD 个人知识库使用场景</n-text>
      <div class="skill-grid">
        <div v-for="s in featuredSkills" :key="s.id" class="skill-card">
          <div class="skill-head">
            <div class="skill-emoji">{{ s.emoji }}</div>
            <n-tag v-if="s.badge" size="tiny" :bordered="false" type="info">{{ s.badge }}</n-tag>
          </div>
          <div class="skill-name">{{ s.name }}</div>
          <div class="skill-desc">{{ s.desc }}</div>
          <div class="skill-actions">
            <n-button size="tiny" type="primary" @click="toggleInstall(s)">{{ installed[s.id] ? '已导入' : '导入' }}</n-button>
          </div>
        </div>
      </div>
    </n-space>

    <n-space v-else-if="skillTab === 'all'" vertical size="medium">
      <n-text depth="3" style="font-size: 12px">浏览全部推荐 Skill</n-text>
      <div class="skill-grid">
        <div v-for="s in allSkills" :key="s.id" class="skill-card">
          <div class="skill-head">
            <div class="skill-emoji">{{ s.emoji }}</div>
            <n-tag size="tiny" :bordered="false">{{ s.category }}</n-tag>
          </div>
          <div class="skill-name">{{ s.name }}</div>
          <div class="skill-desc">{{ s.desc }}</div>
          <div class="skill-actions">
            <n-button size="tiny" type="primary" @click="toggleInstall(s)">{{ installed[s.id] ? '已导入' : '导入' }}</n-button>
          </div>
        </div>
      </div>
    </n-space>

    <n-space v-else vertical size="small">
      <n-empty v-if="Object.keys(installed).length === 0" description="还没有导入 Skill，去推荐首页看看" />
      <div v-for="s in Object.keys(installed)" :key="s">
        <n-text>{{ s }}</n-text>
      </div>
    </n-space>
  </n-modal>
</template>

<style scoped>
.chat-history {
  height: 100%;
  display: flex;
  flex-direction: column;
}
.chat-history-actions {
  padding: 10px 12px 6px;
}
.action-btn {
  height: 36px;
  border: none !important;
  background: transparent !important;
}
.action-btn:hover {
  background: var(--hover-bg) !important;
}
.new-chat-btn {
  background: var(--hover-bg) !important;
  font-weight: 600;
}
.new-chat-btn:hover {
  background: var(--active-bg) !important;
}
.action-btn + .action-btn {
  margin-top: 8px;
}
.chat-history-header {
  padding: 18px 18px 10px;
  display: flex;
  align-items: center;
  border-top: 1px solid var(--border-soft);
  margin-top: 12px;
}
.chat-history-header .title {
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.5px;
  color: var(--text-secondary);
  text-transform: uppercase;
}
.chat-history-list {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  scrollbar-width: thin;
  padding: 8px 12px;
}
.loading-row {
  padding: 12px 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}
.session-item {
  padding: 10px 12px;
  cursor: pointer;
  border-left: 3px solid transparent;
  border-bottom: 1px solid var(--border-soft);
  transition: background 0.15s;
}
.session-item:hover {
  background: var(--hover-bg);
}
.session-item.active {
  border-left-color: #3b82f6;
  background: var(--active-bg);
}
.session-item.active:hover {
  background: var(--active-bg-hover);
}
.session-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  min-width: 0;
}
.session-title {
  font-size: 13px;
  font-weight: 600;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  min-width: 0;
  color: var(--text-primary);
}
.delete-btn {
  padding: 0 4px;
  font-size: 11px;
  flex-shrink: 0;
}
.session-preview {
  font-size: 11px;
  opacity: 0.6;
  margin-top: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--text-secondary);
}
.session-meta {
  font-size: 10px;
  opacity: 0.4;
  margin-top: 4px;
  color: var(--text-muted);
}
.search-item {
  padding: 10px 12px;
  border-radius: 8px;
  border: 1px solid var(--border-soft);
  cursor: pointer;
  transition: background 0.15s;
}
.search-item:hover { background: var(--hover-bg) }
.search-title { font-size: 13px; font-weight: 600; color: var(--text-primary) }
.search-preview { font-size: 12px; opacity: 0.7; margin-top: 4px; color: var(--text-secondary) }
.search-meta { font-size: 11px; opacity: 0.5; margin-top: 4px; color: var(--text-muted) }
.skill-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 12px }
.skill-card { padding: 14px; border: 1px solid var(--border-soft); border-radius: 10px; background: var(--bg-elevated); display: flex; flex-direction: column; gap: 8px }
.skill-card:hover { border-color: var(--accent, #3b82f6) }
.skill-head { display: flex; align-items: center; justify-content: space-between }
.skill-emoji { font-size: 22px }
.skill-name { font-size: 14px; font-weight: 600 }
.skill-desc { font-size: 12px; opacity: 0.75; min-height: 36px; color: var(--text-secondary) }
.skill-actions { display: flex; justify-content: flex-end }
</style>

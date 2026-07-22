<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useSessionsStore } from '@/stores/sessions'
import { useChatStore } from '@/stores/chat'
import { NButton, NPopconfirm, NEmpty, NSpin, NText } from 'naive-ui'

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
</script>

<template>
  <div class="chat-history">
    <div class="chat-history-actions">
      <n-button block @click="newChat" class="action-btn new-chat-btn">+ 新对话</n-button>
      <n-button block quaternary @click="gotoNotes" class="action-btn">知识库</n-button>
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
.chat-history-list {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  scrollbar-width: thin;
  padding: 4px 0;
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
</style>
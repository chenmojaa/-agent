<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useNotesStore } from '@/stores/notes'
import {
  NCard, NSpace, NText, NTag, NInput, NButton, useMessage,
  NPopconfirm, NEmpty, NSpin, NIcon, NUpload, NUploadDragger,
} from 'naive-ui'
import type { UploadFileInfo, UploadCustomRequestOptions } from 'naive-ui'

const notes = useNotesStore()
const message = useMessage()

const tab = ref<'upload' | 'url' | 'text'>('upload')
const urlInput = ref('')
const textInput = ref('')
const textTitle = ref('')
const dragOver = ref(false)

onMounted(() => {
  notes.load()
  notes.refreshStats()
})

async function addUrl() {
  if (!urlInput.value.trim()) return
  try {
    const n = await notes.addUrl(urlInput.value.trim())
    message.success(`已添加：${n.title}`)
    urlInput.value = ''
  } catch (e) {
    message.error((e as Error).message)
  }
}

async function addText() {
  if (!textInput.value.trim()) return
  try {
    const n = await notes.addText(textInput.value, textTitle.value || undefined)
    message.success(`已添加：${n.title}`)
    textInput.value = ''
    textTitle.value = ''
  } catch (e) {
    message.error((e as Error).message)
  }
}

async function uploadOne(file: File) {
  try {
    const n = await notes.uploadFile(file)
    message.success(`已添加：${n.title}`)
  } catch (e) {
    message.error(`${file.name}: ${(e as Error).message}`)
  }
}

function handleDrop(e: DragEvent) {
  e.preventDefault()
  dragOver.value = false
  const files = e.dataTransfer?.files
  if (!files) return
  for (let i = 0; i < files.length; i++) {
    uploadOne(files[i])
  }
}

function handleDragOver(e: DragEvent) {
  e.preventDefault()
  dragOver.value = true
}

function handleDragLeave() {
  dragOver.value = false
}

const uploadHandler = ({ file, onFinish, onError }: UploadCustomRequestOptions) => {
  const f = file.file as File | null
  if (!f) {
    onError()
    return
  }
  notes.uploadFile(f)
    .then(() => onFinish())
    .catch(() => onError())
}

const ACCEPT = '.pdf,.docx,.pptx,.xlsx,.csv,.html,.htm,.txt,.md,.markdown,.png,.jpg,.jpeg,.webp,.bmp,.tif,.tiff'

function formatSize(n: number): string {
  if (n < 1024) return n + ' B'
  if (n < 1024 * 1024) return (n / 1024).toFixed(1) + ' KB'
  return (n / 1024 / 1024).toFixed(2) + ' MB'
}

const typeTag: Record<string, string> = {
  url: 'info',
  text: 'info',
  pdf: 'success',
  image: 'warning',
  docx: 'success',
  pptx: 'info',
  xlsx: 'info',
  csv: 'default',
  html: 'default',
}

function sourceLabel(t: string) {
  if (t === 'image') return '图片/OCR'
  return t.toUpperCase()
}
</script>

<template>
  <div style="height: 100%; display: flex; flex-direction: column; gap: 12px; overflow-y: auto; padding-right: 4px">
    <n-text strong style="font-size: 16px">知识库</n-text>

    <n-card :bordered="false">
      <n-space>
        <n-button :type="tab === 'upload' ? 'primary' : 'default'" @click="tab = 'upload'">上传文件</n-button>
        <n-button :type="tab === 'url' ? 'primary' : 'default'" @click="tab = 'url'">粘贴 URL</n-button>
        <n-button :type="tab === 'text' ? 'primary' : 'default'" @click="tab = 'text'">粘贴文本</n-button>
      </n-space>

      <div v-if="tab === 'upload'" style="margin-top: 12px">
        <div
          @drop="handleDrop"
          @dragover="handleDragOver"
          @dragleave="handleDragLeave"
          :style="{
            padding: '20px',
            textAlign: 'center',
            border: '2px dashed ' + (dragOver ? '#3b82f6' : 'var(--border-soft)'),
            borderRadius: '8px',
            background: dragOver ? 'rgba(59,130,246,0.08)' : 'var(--bg-elevated)',
            transition: 'all 0.2s',
          }"
        >
          <n-text style="font-size: 14px; color: #999">
            拖文件到这里，或
          </n-text>
          <n-upload :accept="ACCEPT" :custom-request="uploadHandler" :show-file-list="false" multiple>
            <n-button>选择文件</n-button>
          </n-upload>
          <div style="margin-top: 10px">
            <n-text depth="3" style="font-size: 12px">
              支持：PDF · DOCX · PPTX · XLSX · CSV · HTML · TXT/MD · 图片（PNG/JPG/WEBP/BMP/TIFF，OCR）
            </n-text>
          </div>
        </div>
        <div v-if="notes.uploadProgress" style="margin-top: 10px; padding: 8px; background: var(--hover-bg); border-radius: 4px">
          <n-spin v-if="notes.uploadProgress.status === 'uploading'" size="small" />
          <n-text v-if="notes.uploadProgress.status === 'done'" type="success">✓ {{ notes.uploadProgress.name }}</n-text>
          <n-text v-else-if="notes.uploadProgress.status === 'failed'" type="error">× {{ notes.uploadProgress.name }}：{{ notes.uploadProgress.message }}</n-text>
          <n-text v-else>{{ notes.uploadProgress.name }} 上传中…</n-text>
        </div>
      </div>

      <div v-else-if="tab === 'url'" style="margin-top: 12px">
        <n-space vertical :size="10">
          <n-input v-model:value="urlInput" placeholder="https://example.com/article" />
          <n-button type="primary" :loading="notes.ingesting" @click="addUrl">抓取并入库</n-button>
        </n-space>
      </div>

      <div v-else-if="tab === 'text'" style="margin-top: 12px">
        <n-space vertical :size="10">
          <n-input v-model:value="textTitle" placeholder="标题（可选）" />
          <n-input
            v-model:value="textInput"
            type="textarea"
            :autosize="{ minRows: 4, maxRows: 12 }"
            placeholder="粘贴文本…"
          />
          <n-button type="primary" :loading="notes.ingesting" @click="addText">入库</n-button>
        </n-space>
      </div>
    </n-card>

    <n-card title="知识库" :bordered="false">
      <div v-if="notes.loading && notes.items.length === 0" style="padding: 12px 4px; display: flex; align-items: center; gap: 8px"><n-spin size="small" /><n-text depth="3" style="font-size: 12px">加载中…</n-text></div>
      <n-empty v-else-if="notes.items.length === 0" description="还没有知识" />

      <n-space vertical v-else>
        <n-card
          v-for="n in notes.items"
          :key="n.id"
          :bordered="false"
          size="small"
          class="item-card"
        >
          <template #header>
            <n-space align="center" justify="space-between" style="width: 100%">
              <n-space align="center" :wrap="false" style="overflow: hidden">
                <n-text strong style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap">{{ n.title }}</n-text>
                <n-tag size="small" :type="(typeTag[n.source_type] as any) || 'default'">{{ sourceLabel(n.source_type) }}</n-tag>
                <n-button v-if="!n.embedded" type="warning" size="tiny" quaternary class="reembed-btn" @click.stop="notes.reembed(n.id).then(() => message.success(String.fromCharCode(24050,26032,20837,20840))).catch(e => message.error(e.message))">未 embedding · 重试</n-button>
                <n-tag v-else size="small" :bordered="false">{{ n.chunk_count }} chunks</n-tag>
              </n-space>
              <n-popconfirm @positive-click="notes.remove(n.id).then(() => message.success('已删除'))">
                <template #trigger>
                  <n-button text size="small" type="error">删除</n-button>
                </template>
                删除该笔记？
              </n-popconfirm>
            </n-space>
          </template>
          <n-text v-if="n.summary" depth="3" style="font-size: 12px">{{ n.summary }}</n-text>
        </n-card>
      </n-space>
    </n-card>
  </div>
</template>

<style scoped>
.item-card {
  background: var(--bg-elevated) !important;
}
</style>
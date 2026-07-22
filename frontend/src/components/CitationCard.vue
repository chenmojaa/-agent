<script setup lang="ts">
import { NCard, NSpace, NTag, NText } from 'naive-ui'
import type { Citation } from '@/api/chat'

defineProps<{ citations: Citation[] }>()
</script>

<template>
  <div class="citations" v-if="citations.length > 0">
    <n-text depth="3" class="citations-title">引用来源</n-text>
    <n-space vertical size="small">
      <n-card
        v-for="(c, i) in citations"
        :key="i"
        size="small"
        :bordered="false"
        class="citation-card"
      >
        <n-space vertical size="small">
          <n-space align="center" :wrap="false">
            <n-tag size="small" :bordered="false">[{{ i + 1 }}]</n-tag>
            <n-text strong style="font-size: 12px">{{ c.title || c.note_id }}</n-text>
            <n-text depth="3" style="font-size: 11px">
              chunk #{{ c.chunk_index }}
              <span v-if="c.score !== undefined"> · score {{ c.score.toFixed(3) }}</span>
            </n-text>
          </n-space>
          <n-text depth="2" style="font-size: 12px; line-height: 1.5; font-style: italic">
            {{ c.snippet }}
          </n-text>
        </n-space>
      </n-card>
    </n-space>
  </div>
</template>

<style scoped>
.citations {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed var(--border-soft);
  max-width: 70%;
}
.citations-title {
  font-size: 11px;
  display: block;
  margin-bottom: 6px;
}
.citation-card {
  background: var(--hover-bg) !important;
}
</style>
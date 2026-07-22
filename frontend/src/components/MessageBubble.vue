<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ role: 'user' | 'assistant' | 'system'; content: string }>()

const displayContent = computed(() => {
  if (!props.content) return ''
  return props.content
    .replace(/<think>[\s\S]*?<\/think>/gi, '')
    .replace(/<think>[\s\S]*$/gi, '')
    .trim()
})
</script>

<template>
  <div :class="['bubble-row', role]">
    <div :class="['bubble', role]">
      {{ displayContent }}
    </div>
  </div>
</template>

<style scoped>
.bubble-row {
  display: flex;
  margin-bottom: 12px;
}
.bubble-row.user { justify-content: flex-end; }
.bubble-row.assistant { justify-content: flex-start; }

.bubble {
  max-width: 70%;
  padding: 10px 14px;
  border-radius: 10px;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 14px;
  line-height: 1.6;
}
.bubble.user {
  background: var(--bg-bubble-user);
  color: var(--text-on-user);
}
.bubble.assistant {
  background: var(--bg-bubble-assistant);
  color: var(--text-primary);
}
.bubble.system {
  background: var(--bg-bubble-thinking);
  color: var(--text-muted);
  font-style: italic;
}
</style>
import { defineStore } from 'pinia'

export type ReasoningLevel = 'low' | 'medium' | 'high' | 'xhigh'

export interface CustomModelEntry {
  id: string
  name: string
  baseUrl: string
  apiKey: string
  provider: string
  models: { name: string; reasoning: ReasoningLevel }[]
  defaultModel: string
  embeddingModel?: string   // optional: separate model for embeddings (MiniMax uses embo-01 etc.)
  createdAt: string
}

const STORAGE_KEY = 'sb_custom_models'
const SELECTED_KEY = 'sb_selected_model'

function load(): CustomModelEntry[] {
  try {
    const s = localStorage.getItem(STORAGE_KEY)
    return s ? JSON.parse(s) : []
  } catch { return [] }
}

function save(list: CustomModelEntry[]) {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(list)) } catch {}
}

function loadSelected(): string | null {
  try { return localStorage.getItem(SELECTED_KEY) } catch { return null }
}

interface State {
  list: CustomModelEntry[]
  selectedId: string | null
}

export const useModelsStore = defineStore('models', {
  state: (): State => {
    const list = load()
    let selectedId = loadSelected()
    if (!selectedId && list.length > 0) selectedId = list[0].id
    return { list, selectedId }
  },
  getters: {
    selected(state): (CustomModelEntry & { modelName: string; reasoning: ReasoningLevel }) | null {
      const e = state.list.find(x => x.id === state.selectedId) || state.list[0]
      if (!e) return null
      const m = e.models.find(x => x.name === e.defaultModel) || e.models[0]
      return { ...e, modelName: m?.name || '', reasoning: m?.reasoning || 'medium' }
    },
  },
  actions: {
    persist() { save(this.list) },
    add(entry: CustomModelEntry) {
      this.list.push(entry)
      if (!this.selectedId) this.selectedId = entry.id
      this.persist()
    },
    update(id: string, patch: Partial<CustomModelEntry>) {
      const i = this.list.findIndex(x => x.id === id)
      if (i >= 0) {
        this.list[i] = { ...this.list[i], ...patch }
        this.persist()
      }
    },
    remove(id: string) {
      this.list = this.list.filter(x => x.id !== id)
      if (this.selectedId === id) {
        this.selectedId = this.list[0]?.id ?? null
        try {
          if (this.selectedId) localStorage.setItem(SELECTED_KEY, this.selectedId)
          else localStorage.removeItem(SELECTED_KEY)
        } catch {}
      }
      this.persist()
    },
    select(id: string | null) {
      this.selectedId = id
      try {
        if (id) localStorage.setItem(SELECTED_KEY, id)
        else localStorage.removeItem(SELECTED_KEY)
      } catch {}
    },
  },
})

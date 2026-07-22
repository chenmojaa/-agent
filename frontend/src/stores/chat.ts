import { defineStore } from 'pinia'
import { chatStream, stripThink, type ChatMessage, type Citation } from '@/api/chat'
import { useSettingsStore } from './settings'
import { useModelsStore } from './models'
import { useSessionsStore } from './sessions'

interface Msg extends ChatMessage { id: string; citations?: Citation[] }
interface State {
  sessionId: string | null
  messages: Msg[]
  isStreaming: boolean
  error: string | null
  useRag: boolean
}

export const useChatStore = defineStore("chat", {
  state: (): State => ({
    sessionId: null,
    isStreaming: false,
    messages: [],
    error: null,
    useRag: true,
  }),
  actions: {
    toggleRag() { this.useRag = !this.useRag },
    async send(text: string) {
      if (!text.trim() || this.isStreaming) return
      const userMsg: Msg = { id: "u-" + String(Date.now()), role: "user", content: text }
      const asstMsg: Msg = { id: "a-" + String(Date.now() + 1), role: "assistant", content: "" }
      this.messages.push(userMsg, asstMsg)
      this.isStreaming = true
      this.error = null

      const models = useModelsStore()
      const sessions = useSessionsStore()
      const history: ChatMessage[] = this.messages
        .filter(m => m.id !== asstMsg.id)
        .map(m => ({ role: m.role, content: m.content }))

      const sel = models.selected
      const provider = sel?.provider
      const model = sel?.modelName
      const baseUrl = sel?.baseUrl
      const apiKey = sel?.apiKey
      const reasoning = sel?.reasoning

      try {
        const stream = chatStream({
          messages: history,
          provider: provider ?? null,
          model: model ?? null,
          use_rag: this.useRag,
          session_id: this.sessionId,
          base_url: baseUrl ?? null,
          api_key: apiKey ?? null,
          reasoning_level: reasoning ?? null,
        })
        // 累积原始（含 <think>），渲染前 strip
        let rawAccumulated = ""
        for await (const ev of stream) {
          if (ev.type === "session" && ev.session_id) {
            this.sessionId = ev.session_id
            sessions.load()
          } else if (ev.type === "delta" && typeof ev.data === "string") {
            rawAccumulated += ev.data
            asstMsg.content = stripThink(rawAccumulated)
            const idx = this.messages.findIndex(m => m.id === asstMsg.id)
            if (idx >= 0) this.messages[idx] = { ...asstMsg }
          } else if (ev.type === "citations" && Array.isArray(ev.data)) {
            asstMsg.citations = ev.data as Citation[]
            const idx = this.messages.findIndex(m => m.id === asstMsg.id)
            if (idx >= 0) this.messages[idx] = { ...asstMsg }
          } else if (ev.type === "error") {
            const msg = (ev.data && typeof ev.data === "string") ? ev.data : String(ev.data ?? "unknown error")
            rawAccumulated += "\n\n[Error] " + msg
            asstMsg.content = stripThink(rawAccumulated)
            const idx = this.messages.findIndex(m => m.id === asstMsg.id)
            if (idx >= 0) this.messages[idx] = { ...asstMsg }
            this.error = msg
          } else if (ev.type === "done") {
            break
          }
        }
        sessions.load()
      } catch (e) {
        const errMsg = (e as Error).message || String(e)
        this.error = errMsg
        rawAccumulated += "\n\n[Error] " + errMsg
        asstMsg.content = stripThink(rawAccumulated)
        const idx = this.messages.findIndex(m => m.id === asstMsg.id)
        if (idx >= 0) this.messages[idx] = { ...asstMsg }
      } finally {
        this.isStreaming = false
      }
    },
    async loadFromSession(sessionId: string) {
      const sessions = useSessionsStore()
      await sessions.loadDetail(sessionId)
      const detail = sessions.currentDetail
      if (!detail) { this.error = "Session not found"; return }
      this.sessionId = detail.id
      this.messages = detail.messages.map(m => ({
        id: "h-" + String(m.id),
        role: m.role as "user" | "assistant" | "system",
        content: stripThink(m.content),
        citations: m.citations || undefined,
      }))
      this.error = null
    },
    clear() {
      this.sessionId = null
      this.messages = []
      this.error = null
    },
  },
})
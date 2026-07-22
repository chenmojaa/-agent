import { defineStore } from 'pinia'
import { listSessions, createSession, deleteSession, getSessionDetail, type Session, type SessionDetail } from '@/api/sessions'

interface State {
  items: Session[]
  loading: boolean
  error: string | null
  currentDetail: SessionDetail | null
}

export const useSessionsStore = defineStore("sessions", {
  state: (): State => ({ items: [], loading: false, error: null, currentDetail: null }),
  actions: {
    async load() {
      this.loading = true
      this.error = null
      try { this.items = await listSessions() }
      catch (e) { this.error = (e as Error).message }
      finally { this.loading = false }
    },
    async createNew(title?: string) {
      const s = await createSession(title)
      this.items.unshift({
        ...s,
        message_count: 0,
        preview: "",
        updated_at: s.created_at,
      })
      return s
    },
    async remove(id: string) {
      try {
        await deleteSession(id)
        this.items = this.items.filter(s => s.id !== id)
        if (this.currentDetail?.id === id) this.currentDetail = null
      } catch (e) {
        this.error = (e as Error).message
      }
    },
    async loadDetail(id: string) {
      this.loading = true
      try {
        this.currentDetail = await getSessionDetail(id)
      } catch (e) {
        this.error = (e as Error).message
      } finally {
        this.loading = false
      }
    },
    clearDetail() { this.currentDetail = null },
  },
})
import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", redirect: "/chat" },
    { path: "/chat", name: "chat", component: () => import("@/views/ChatView.vue") },
    { path: "/chat/:id", name: "chat-id", component: () => import("@/views/ChatView.vue") },
    { path: "/notes", name: "notes", component: () => import("@/views/NotesView.vue") },
    { path: "/settings", name: "settings", component: () => import("@/views/SettingsView.vue") },
  ],
})

export default router
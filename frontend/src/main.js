import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router/index.js'
import App from './App.vue'
import './style.css'

const app = createApp(App)
const pinia = createPinia()
app.use(pinia)
app.use(router)
app.mount('#app')

// Auto-load user history from DB on app start
import { useUserStore } from './stores/user'
const userStore = useUserStore()
userStore.initializeSession()

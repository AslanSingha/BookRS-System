<template>
  <div class="min-h-screen bg-gray-50">
    <nav class="bg-white shadow-sm border-b border-gray-100 sticky top-0 z-50">
      <div class="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
        <router-link to="/" class="flex items-center gap-2">
          <span class="text-2xl">📚</span>
          <span class="font-bold text-xl text-primary-700">BookRS</span>
        </router-link>

        <div class="flex-1 max-w-xl mx-6">
          <form @submit.prevent="handleSearch" class="relative">
            <input v-model="searchQuery" type="text"
              placeholder="Search books by title, author, or topic..."
              class="w-full pl-4 pr-10 py-2 rounded-full border border-gray-200 focus:outline-none focus:border-primary-500 focus:ring-1 focus:ring-primary-500 text-sm" />
            <button type="submit" class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-primary-600">🔍</button>
          </form>
        </div>

        <div class="flex items-center gap-4 text-sm font-medium">
          <router-link to="/" class="text-gray-600 hover:text-primary-600">Home</router-link>
          <router-link to="/trending" class="text-gray-600 hover:text-primary-600">📈 Trending</router-link>
          <router-link to="/popular" class="text-gray-600 hover:text-primary-600">🔥 Popular</router-link>

          <div v-if="userStore.isLoggedIn" class="flex items-center gap-2">
            <router-link to="/profile" class="flex items-center gap-1 text-gray-600 hover:text-primary-600">
              👤 {{ userStore.userId }}
              <span v-if="userStore.ratedBooks.size > 0"
                class="bg-primary-100 text-primary-700 text-xs px-1.5 py-0.5 rounded-full">
                {{ userStore.ratedBooks.size }}⭐
              </span>
            </router-link>
            <button @click="userStore.logout()" class="text-xs text-red-500 hover:text-red-700">Logout</button>
          </div>
          <button v-else @click="showLogin = true"
            class="bg-primary-600 text-white px-4 py-1.5 rounded-full hover:bg-primary-700 transition-colors">
            Login
          </button>
        </div>
      </div>
    </nav>

    <!-- Login Modal -->
    <div v-if="showLogin" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white rounded-2xl p-6 w-96 shadow-xl">
        <h2 class="text-xl font-bold mb-2">Login to BookRS</h2>
        <p class="text-sm text-gray-500 mb-4">Enter any username to get personalized recommendations</p>
        <input v-model="loginId" type="text"
          placeholder="Enter username (e.g. rin, john123)"
          class="w-full px-4 py-2 border border-gray-200 rounded-lg mb-4 focus:outline-none focus:border-primary-500"
          @keyup.enter="handleLogin" />
        <div class="flex gap-3">
          <button @click="handleLogin" class="flex-1 bg-primary-600 text-white py-2 rounded-lg hover:bg-primary-700">Login</button>
          <button @click="showLogin = false" class="flex-1 bg-gray-100 text-gray-600 py-2 rounded-lg hover:bg-gray-200">Cancel</button>
        </div>
      </div>
    </div>

    <main class="max-w-7xl mx-auto px-4 py-6">
      <router-view />
    </main>

    <footer class="mt-12 py-6 border-t border-gray-100 text-center text-sm text-gray-400">
      BookRS — AI-Powered Book Recommendation System | ITC Cambodia Master's Thesis 2025
    </footer>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from './stores/user'

const router = useRouter()
const userStore = useUserStore()
const searchQuery = ref('')
const showLogin = ref(false)
const loginId = ref('')

function handleSearch() {
  if (searchQuery.value.trim()) {
    router.push({ name: 'Search', query: { q: searchQuery.value } })
    searchQuery.value = ''
  }
}

function handleLogin() {
  if (loginId.value.trim()) {
    userStore.login(loginId.value.trim())
    showLogin.value = false
    loginId.value = ''
  }
}
</script>

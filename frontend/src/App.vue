<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Navbar -->
    <nav class="bg-white shadow-sm border-b border-gray-100 sticky top-0 z-50">
      <div class="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
        <!-- Logo -->
        <router-link to="/" class="flex items-center gap-2">
          <span class="text-2xl">📚</span>
          <span class="font-bold text-xl text-primary-700">BookRS</span>
        </router-link>

        <!-- Search bar -->
        <div class="flex-1 max-w-xl mx-6">
          <form @submit.prevent="handleSearch" class="relative">
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Search books by title, author, or topic..."
              class="w-full pl-4 pr-10 py-2 rounded-full border border-gray-200 focus:outline-none focus:border-primary-500 focus:ring-1 focus:ring-primary-500 text-sm"
            />
            <button type="submit" class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-primary-600">
              🔍
            </button>
          </form>
        </div>

        <!-- Nav links -->
        <div class="flex items-center gap-4 text-sm font-medium">
          <router-link to="/" class="text-gray-600 hover:text-primary-600">Home</router-link>
          <router-link to="/trending" class="text-gray-600 hover:text-primary-600">📈 Trending</router-link>
          <router-link to="/popular" class="text-gray-600 hover:text-primary-600">🔥 Popular</router-link>
        </div>
      </div>
    </nav>

    <!-- Main content -->
    <main class="max-w-7xl mx-auto px-4 py-6">
      <router-view />
    </main>

    <!-- Footer -->
    <footer class="mt-12 py-6 border-t border-gray-100 text-center text-sm text-gray-400">
      BookRS — AI-Powered Book Recommendation System | ITC Cambodia Master's Thesis
    </footer>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const searchQuery = ref('')

function handleSearch() {
  if (searchQuery.value.trim()) {
    router.push({ name: 'Search', query: { q: searchQuery.value } })
    searchQuery.value = ''
  }
}
</script>

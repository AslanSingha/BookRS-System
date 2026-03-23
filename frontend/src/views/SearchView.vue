<template>
  <div>
    <h1 class="text-2xl font-bold mb-6">🔍 Search Books</h1>

    <!-- Search bar -->
    <form @submit.prevent="handleSearch" class="mb-8">
      <div class="flex gap-3">
        <input
          v-model="query"
          type="text"
          placeholder="Search by title, author, topic, genre..."
          class="flex-1 px-4 py-3 rounded-xl border border-gray-200 focus:outline-none focus:border-primary-500 focus:ring-1 focus:ring-primary-500"
        />
        <button type="submit" class="btn-primary px-6 py-3 rounded-xl">Search</button>
      </div>
    </form>

    <!-- Results -->
    <div v-if="query || store.searchResults.length > 0">
      <div class="flex items-center justify-between mb-4">
        <h2 class="font-semibold text-gray-700">
          {{ store.searchResults.length }} results for "{{ lastQuery }}"
        </h2>
        <span class="text-sm text-gray-400">Semantic search powered by SBERT</span>
      </div>
      <BookGrid :books="store.searchResults" :is-loading="store.isLoading" />
    </div>

    <!-- Empty state -->
    <div v-else class="text-center py-16 text-gray-400">
      <p class="text-5xl mb-4">🔍</p>
      <p class="text-lg">Search for any book, author, or topic</p>
      <p class="text-sm mt-2">BookRS uses semantic search to find what you mean, not just what you type</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useBookStore } from '../stores/books'
import BookGrid from '../components/BookGrid.vue'

const store = useBookStore()
const route = useRoute()
const query = ref('')
const lastQuery = ref('')

async function handleSearch() {
  if (!query.value.trim()) return
  lastQuery.value = query.value
  await store.search(query.value)
}

onMounted(() => {
  if (route.query.q) {
    query.value = route.query.q
    handleSearch()
  }
})
</script>

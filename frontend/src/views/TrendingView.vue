<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <div class="flex items-center gap-3">
        <span class="text-3xl">📈</span>
        <div>
          <h1 class="text-2xl font-bold">Trending Books</h1>
          <p class="text-sm text-gray-500">Highly rated books with strong reader engagement</p>
        </div>
      </div>
      <button @click="refresh"
        class="text-sm text-primary-600 hover:text-primary-700 flex items-center gap-1">
        🔄 Refresh
      </button>
    </div>
    <BookGrid :books="store.trending" :is-loading="store.isLoading" />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useBookStore } from '../stores/books'
import BookGrid from '../components/BookGrid.vue'

const store = useBookStore()

function refresh() {
  store.fetchTrending()
}

onMounted(() => store.fetchTrending())
</script>

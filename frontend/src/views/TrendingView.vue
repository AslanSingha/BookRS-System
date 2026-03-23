<template>
  <div>
    <div class="flex items-center gap-3 mb-6">
      <span class="text-3xl">📈</span>
      <div>
        <h1 class="text-2xl font-bold">Trending Books</h1>
        <p class="text-sm text-gray-500">Highly rated books with strong reader engagement</p>
      </div>
    </div>
    <BookGrid :books="store.trending" :is-loading="store.isLoading" />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useBookStore } from '../stores/books'
import BookGrid from '../components/BookGrid.vue'

const store = useBookStore()
onMounted(() => store.fetchTrending())
</script>

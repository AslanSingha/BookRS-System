<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <div>
        <div class="flex items-center gap-2 mb-1">
          <svg class="w-5 h-5 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"/>
          </svg>
          <h1 class="text-2xl font-bold text-slate-900">Trending Now</h1>
        </div>
        <p class="text-sm text-slate-500">
          Highly rated books scored by quality and engagement · refreshes every 10 minutes
        </p>
      </div>
      <button @click="store.fetchTrending()"
        class="flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-700 transition-colors bg-white border border-slate-200 px-3 py-1.5 rounded-lg">
        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
        </svg>
        Refresh
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
onMounted(() => store.fetchTrending())
</script>

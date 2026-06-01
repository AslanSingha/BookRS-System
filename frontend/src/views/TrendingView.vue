<template>
  <div>
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <div class="flex items-center gap-2 mb-1">
          <svg class="w-5 h-5 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"/>
          </svg>
          <h1 class="text-2xl font-bold text-slate-900">Trending Now</h1>
        </div>
        <p class="text-sm text-slate-500">
          Scored by rating quality × engagement · updates every 10 minutes
        </p>
      </div>
      <button @click="refresh"
        class="flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-700
          transition-colors bg-white border border-slate-200 px-3 py-1.5 rounded-lg">
        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
        </svg>
        Refresh
      </button>
    </div>

    <!-- Sort bar -->
    <div class="flex items-center justify-between mb-5">
      <p class="text-xs text-slate-400">
        Showing {{ visibleBooks.length }} of {{ sortedBooks.length }} books
      </p>
      <div class="flex items-center gap-2">
        <span class="text-xs text-slate-400">Sort by</span>
        <div class="flex gap-1">
          <button v-for="s in sortOptions" :key="s.value"
            @click="selectedSort = s.value; currentPage = 1"
            class="px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1"
            :class="selectedSort === s.value
              ? 'bg-slate-900 text-white'
              : 'bg-white border border-slate-200 text-slate-600 hover:border-slate-300'">
            {{ s.label }}
            <svg v-if="selectedSort === s.value" class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- Grid -->
    <BookGrid :books="visibleBooks" :is-loading="store.isLoading" />

    <!-- Load more -->
    <div v-if="visibleBooks.length < sortedBooks.length" class="flex justify-center mt-8">
      <button @click="currentPage++"
        class="flex items-center gap-2 px-6 py-2.5 bg-white border border-slate-200
          rounded-xl text-sm font-medium text-slate-600 hover:border-slate-300
          hover:bg-slate-50 transition-all">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
        </svg>
        Load more
        <span class="text-slate-400 text-xs">
          ({{ sortedBooks.length - visibleBooks.length }} remaining)
        </span>
      </button>
    </div>

    <div v-else-if="sortedBooks.length > 0" class="flex justify-center mt-8">
      <p class="text-xs text-slate-400">All {{ sortedBooks.length }} books loaded</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useBookStore } from '../stores/books'
import BookGrid from '../components/BookGrid.vue'

const store = useBookStore()
const selectedSort = ref('score')
const pageSize = 20
const currentPage = ref(1)

const sortOptions = [
  { value: 'score', label: 'Trending score' },
  { value: 'rating', label: 'Highest rated' },
  { value: 'title', label: 'Title A–Z' },
]

const sortedBooks = computed(() => {
  const books = [...store.trending]
  if (selectedSort.value === 'rating') {
    return books.sort((a, b) => b.avg_rating - a.avg_rating)
  }
  if (selectedSort.value === 'title') {
    return books.sort((a, b) => a.title.localeCompare(b.title))
  }
  return books // default = trending score (API order)
})

const visibleBooks = computed(() => {
  return sortedBooks.value.slice(0, currentPage.value * pageSize)
})

async function refresh() {
  currentPage.value = 1
  await store.fetchTrending()
}

onMounted(() => store.fetchTrending(100))
</script>

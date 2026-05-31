<template>
  <div>
    <div class="mb-6">
      <div class="flex items-center gap-2 mb-1">
        <svg class="w-5 h-5 text-rose-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7C14 5 16.09 5.777 17.656 7.343A7.975 7.975 0 0120 13a7.975 7.975 0 01-2.343 5.657z"/>
        </svg>
        <h1 class="text-2xl font-bold text-slate-900">Most Popular</h1>
      </div>
      <p class="text-sm text-slate-500">Books loved by the most readers worldwide</p>
    </div>

    <!-- Genre filters -->
    <div class="flex gap-2 flex-wrap mb-6">
      <button v-for="g in genres" :key="g.value"
        @click="selectGenre(g.value)"
        class="px-3 py-1.5 rounded-lg text-xs font-medium transition-all"
        :class="selectedGenre === g.value
          ? 'bg-slate-900 text-white'
          : 'bg-white border border-slate-200 text-slate-600 hover:border-slate-300'">
        {{ g.label }}
      </button>
    </div>

    <BookGrid :books="store.popular" :is-loading="store.isLoading" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useBookStore } from '../stores/books'
import BookGrid from '../components/BookGrid.vue'

const store = useBookStore()
const selectedGenre = ref(null)

const genres = [
  { value: null, label: 'All' },
  { value: 'fiction', label: 'Fiction' },
  { value: 'non-fiction', label: 'Non-Fiction' },
  { value: 'romance', label: 'Romance' },
  { value: 'fantasy, paranormal', label: 'Fantasy' },
  { value: 'mystery, thriller, crime', label: 'Mystery' },
  { value: 'history, historical fiction, biography', label: 'History' },
  { value: 'children', label: 'Children' },
  { value: 'young-adult', label: 'Young Adult' },
  { value: 'science, technology, engineering, mathematics', label: 'STEM' },
]

function selectGenre(genre) {
  selectedGenre.value = genre
  store.fetchPopular(genre)
}

onMounted(() => store.fetchPopular())
</script>

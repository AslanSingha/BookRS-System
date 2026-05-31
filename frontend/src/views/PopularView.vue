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

    <!-- Filters + Sort row -->
    <div class="flex flex-wrap items-center justify-between gap-3 mb-6">
      <!-- Genre filters -->
      <div class="flex gap-2 flex-wrap">
        <button v-for="g in genres" :key="g.value"
          @click="selectGenre(g.value)"
          class="px-3 py-1.5 rounded-lg text-xs font-medium transition-all"
          :class="selectedGenre === g.value
            ? 'bg-slate-900 text-white'
            : 'bg-white border border-slate-200 text-slate-600 hover:border-slate-300'">
          {{ g.label }}
        </button>
      </div>

      <!-- Sort -->
      <div class="flex items-center gap-2">
        <span class="text-xs text-slate-400">Sort by</span>
        <div class="flex gap-1">
          <button v-for="s in sortOptions" :key="s.value"
            @click="selectSort(s.value)"
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

    <!-- Book count -->
    <p class="text-xs text-slate-400 mb-4">
      Showing {{ visibleBooks.length }} of {{ sortedBooks.length }} books
    </p>

    <!-- Grid -->
    <BookGrid :books="visibleBooks" :is-loading="store.isLoading" />

    <!-- Load more -->
    <div v-if="visibleBooks.length < sortedBooks.length" class="flex justify-center mt-8">
      <button @click="loadMore"
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

    <!-- All loaded -->
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
const selectedGenre = ref(null)
const selectedSort = ref('most_rated')
const pageSize = 20
const currentPage = ref(1)

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

const sortOptions = [
  { value: 'most_rated', label: 'Most rated' },
  { value: 'highest_rated', label: 'Highest rated' },
]

const sortedBooks = computed(() => {
  const books = [...store.popular]
  if (selectedSort.value === 'highest_rated') {
    return books.sort((a, b) => b.avg_rating - a.avg_rating)
  }
  return books // default = most rated (API order)
})

const visibleBooks = computed(() => {
  return sortedBooks.value.slice(0, currentPage.value * pageSize)
})

function loadMore() {
  currentPage.value++
}

async function selectGenre(genre) {
  selectedGenre.value = genre
  currentPage.value = 1
  await store.fetchPopular(genre, 100) // fetch 100 for load more
}

function selectSort(sort) {
  selectedSort.value = sort
  currentPage.value = 1
}

onMounted(() => store.fetchPopular(null, 100))
</script>

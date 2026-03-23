<template>
  <div>
    <div class="flex items-center gap-3 mb-6">
      <span class="text-3xl">🔥</span>
      <div>
        <h1 class="text-2xl font-bold">Most Popular Books</h1>
        <p class="text-sm text-gray-500">Books loved by the most readers</p>
      </div>
    </div>

    <!-- Genre filter -->
    <div class="flex gap-2 flex-wrap mb-6">
      <button
        v-for="g in genres"
        :key="g"
        @click="selectGenre(g)"
        :class="[
          'px-3 py-1 rounded-full text-sm font-medium transition-colors',
          selectedGenre === g
            ? 'bg-primary-600 text-white'
            : 'bg-white text-gray-600 border border-gray-200 hover:border-primary-400'
        ]"
      >
        {{ g === null ? 'All' : g }}
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
const genres = [null, 'fiction', 'non-fiction', 'romance', 'fantasy, paranormal',
                'mystery, thriller, crime', 'history, historical fiction, biography',
                'children', 'young-adult', 'poetry',
                'science, technology, engineering, mathematics']

function selectGenre(genre) {
  selectedGenre.value = genre
  store.fetchPopular(genre)
}

onMounted(() => store.fetchPopular())
</script>

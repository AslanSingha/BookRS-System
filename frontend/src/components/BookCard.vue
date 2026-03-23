<template>
  <router-link :to="`/book/${book.book_id}`" class="book-card block overflow-hidden">
    <!-- Cover image -->
    <div class="relative h-48 bg-gradient-to-br from-primary-100 to-primary-200 flex items-center justify-center overflow-hidden">
      <img
        v-if="book.image_url && !imgError"
        :src="book.image_url"
        :alt="book.title"
        class="w-full h-full object-cover"
        @error="imgError = true"
      />
      <span v-else class="text-5xl">📖</span>

      <!-- Genre badge -->
      <span v-if="book.genre" class="absolute top-2 left-2 bg-white/90 text-xs px-2 py-0.5 rounded-full text-primary-700 font-medium">
        {{ formatGenre(book.genre) }}
      </span>
    </div>

    <!-- Info -->
    <div class="p-3">
      <h3 class="font-semibold text-sm text-gray-900 line-clamp-2 mb-1">{{ book.title }}</h3>
      <p class="text-xs text-gray-500 mb-2">{{ book.authors }}</p>

      <div class="flex items-center justify-between">
        <div class="flex items-center gap-1">
          <span class="text-yellow-400 text-xs">★</span>
          <span class="text-xs text-gray-600">{{ book.avg_rating?.toFixed(1) || 'N/A' }}</span>
        </div>
        <span v-if="book.reason" class="text-xs text-primary-600 bg-primary-50 px-2 py-0.5 rounded-full">
          {{ reasonLabel(book.reason) }}
        </span>
      </div>
    </div>
  </router-link>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  book: { type: Object, required: true }
})

const imgError = ref(false)

function formatGenre(genre) {
  const map = {
    'fiction': 'Fiction',
    'non-fiction': 'Non-Fiction',
    'romance': 'Romance',
    'fantasy, paranormal': 'Fantasy',
    'mystery, thriller, crime': 'Mystery',
    'history, historical fiction, biography': 'History',
    'children': 'Children',
    'comics, graphic': 'Comics',
    'young-adult': 'Young Adult',
    'poetry': 'Poetry',
    'science, technology, engineering, mathematics': 'STEM',
  }
  return map[genre] || genre
}

function reasonLabel(reason) {
  const map = {
    'hybrid': '✨ For You',
    'content': '📖 Similar',
    'popular': '🔥 Popular',
    'trending': '📈 Trending',
    'search': '🔍 Match',
  }
  return map[reason] || reason
}
</script>

<template>
  <div v-if="book" class="max-w-4xl mx-auto">
    <div class="card mb-6">
      <div class="flex gap-6">
        <!-- Cover -->
        <div class="w-44 h-64 bg-gradient-to-br from-primary-100 to-primary-200 rounded-xl flex-shrink-0 flex items-center justify-center overflow-hidden shadow-md">
          <img v-if="book.image_url && !imgError"
               :src="book.image_url" :alt="book.title"
               class="w-full h-full object-cover"
               @error="imgError = true" />
          <span v-else class="text-6xl">📖</span>
        </div>

        <!-- Info -->
        <div class="flex-1">
          <span v-if="book.genre" class="text-xs bg-primary-50 text-primary-700 px-3 py-1 rounded-full font-medium">
            {{ book.genre }}
          </span>
          <h1 class="text-2xl font-bold mt-2 mb-1">{{ book.title }}</h1>
          <p class="text-gray-500 mb-3">by {{ book.authors }}</p>

          <div class="flex items-center gap-4 mb-4">
            <div class="flex items-center gap-1">
              <span class="text-yellow-400 text-lg">★</span>
              <span class="font-bold text-lg">{{ book.avg_rating?.toFixed(2) }}</span>
            </div>
            <span class="text-gray-400 text-sm">{{ book.ratings_count?.toLocaleString() }} ratings</span>
            <span v-if="book.isbn13" class="text-gray-400 text-sm">ISBN: {{ book.isbn13 }}</span>
          </div>

          <!-- Action buttons -->
          <div class="flex gap-3 mb-4">
            <button @click="handleFavorite"
              :class="[
                'flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm transition-colors',
                isFavorited
                  ? 'bg-red-50 text-red-600 border border-red-200'
                  : 'bg-gray-50 text-gray-600 border border-gray-200 hover:border-red-300'
              ]">
              {{ isFavorited ? '❤️ Favorited' : '🤍 Add to Favorites' }}
            </button>
          </div>

          <!-- Rate this book -->
          <div class="mb-4">
            <p class="text-sm font-medium text-gray-700 mb-2">
              {{ userStore.isLoggedIn ? 'Your Rating:' : 'Login to rate this book' }}
            </p>
            <div v-if="userStore.isLoggedIn" class="flex gap-1 items-center">
              <button v-for="star in 5" :key="star"
                @click="handleRating(star)"
                class="text-2xl transition-transform hover:scale-110"
                :class="star <= thisBookRating ? 'text-yellow-400' : 'text-gray-300'">
                ★
              </button>
              <span v-if="thisBookRating" class="ml-2 text-sm text-green-600 font-medium">
                {{ thisBookRating }}/5 saved!
              </span>
            </div>
          </div>

          <p class="text-gray-700 text-sm leading-relaxed">{{ book.description }}</p>
        </div>
      </div>
    </div>

    <!-- Similar books -->
    <section>
      <h2 class="text-xl font-bold mb-4">📖 Similar Books</h2>
      <BookGrid :books="similar" :is-loading="loadingSimilar" />
    </section>
  </div>

  <div v-else-if="loading" class="text-center py-16">
    <div class="text-4xl mb-4 animate-bounce">📚</div>
    <p class="text-gray-400">Loading book...</p>
  </div>

  <div v-else class="text-center py-16 text-gray-400">
    <p class="text-4xl mb-3">😕</p>
    <p>Book not found</p>
    <router-link to="/" class="text-primary-600 hover:underline text-sm mt-2 inline-block">Go Home</router-link>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { booksApi, recommendApi } from '../services/api'
import { useUserStore } from '../stores/user'
import { useBookStore } from '../stores/books'
import BookGrid from '../components/BookGrid.vue'

const route = useRoute()
const userStore = useUserStore()
const bookStore = useBookStore()
const book = ref(null)
const similar = ref([])
const imgError = ref(false)
const loadingSimilar = ref(false)
const loading = ref(true)

// Rating is per-book — computed from store, not shared state
const thisBookRating = computed(() =>
  userStore.ratedBooks.get(route.params.id) || 0
)

const isFavorited = computed(() =>
  userStore.favorites.has(route.params.id)
)

async function loadBook(id) {
  loading.value = true
  imgError.value = false
  book.value = null
  similar.value = []

  try {
    const res = await booksApi.getBook(id)
    book.value = res.data
    await userStore.logView(id)

    loadingSimilar.value = true
    const simRes = await recommendApi.getSimilar(id, 12)
    similar.value = simRes.data.recommendations
  } catch (e) {
    console.error('Failed to load book:', e)
    book.value = null
  } finally {
    loading.value = false
    loadingSimilar.value = false
  }
}

async function handleFavorite() {
  if (!userStore.isLoggedIn) {
    alert('Please login to add favorites!')
    return
  }
  await userStore.toggleFavorite(route.params.id)
}

async function handleRating(star) {
  // Only rate THIS book — not similar books
  const bookId = route.params.id
  await userStore.rateBook(bookId, star)
  // Refresh home recommendations in background
  bookStore.fetchRecommendations()
}

onMounted(() => loadBook(route.params.id))
watch(() => route.params.id, (id) => {
  if (id) loadBook(id)
})
</script>

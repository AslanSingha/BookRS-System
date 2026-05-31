<template>
  <div v-if="book" class="max-w-4xl mx-auto">

    <!-- Breadcrumb -->
    <div class="flex items-center gap-2 text-xs text-slate-400 mb-6">
      <router-link to="/" class="hover:text-slate-600 transition-colors">Home</router-link>
      <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
      </svg>
      <span class="text-slate-600 truncate max-w-xs">{{ book.title }}</span>
    </div>

    <!-- Main card -->
    <div class="bg-white border border-slate-100 rounded-2xl p-6 mb-8">
      <div class="flex gap-6">

        <!-- Cover -->
        <div class="w-36 flex-shrink-0">
          <div class="rounded-xl overflow-hidden shadow-book bg-slate-100" style="aspect-ratio:2/3">
            <img v-if="isValidUrl && !imgError"
              :src="book.image_url" :alt="book.title"
              class="w-full h-full object-cover"
              @error="imgError = true" />
            <div v-else class="w-full h-full flex items-center justify-center bg-gradient-to-br from-slate-100 to-slate-200">
              <svg class="w-8 h-8 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
              </svg>
            </div>
          </div>
        </div>

        <!-- Info -->
        <div class="flex-1 min-w-0">
          <!-- Genre -->
          <span v-if="book.genre"
            class="inline-block text-xs font-medium px-2.5 py-1 rounded-md bg-primary-50 text-primary-700 mb-3">
            {{ formatGenre(book.genre) }}
          </span>

          <h1 class="text-2xl font-bold text-slate-900 leading-tight mb-1">{{ book.title }}</h1>
          <p class="text-slate-500 mb-4">by <span class="font-medium text-slate-700">{{ book.authors }}</span></p>

          <!-- Stats row -->
          <div class="flex items-center gap-4 mb-5">
            <div class="flex items-center gap-1.5">
              <div class="flex items-center gap-0.5">
                <svg v-for="i in 5" :key="i"
                  class="w-4 h-4"
                  :class="i <= Math.round(book.avg_rating) ? 'text-amber-400 fill-amber-400' : 'text-slate-200 fill-slate-200'"
                  viewBox="0 0 20 20">
                  <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"/>
                </svg>
              </div>
              <span class="text-sm font-semibold text-slate-700">{{ book.avg_rating?.toFixed(2) }}</span>
            </div>
            <span class="text-xs text-slate-400">{{ book.ratings_count?.toLocaleString() }} ratings</span>
            <span v-if="book.isbn13" class="text-xs text-slate-400">ISBN: {{ book.isbn13 }}</span>
          </div>

          <!-- Actions -->
          <div v-if="userStore.isLoggedIn" class="flex flex-wrap gap-2 mb-5">
            <!-- Favorite -->
            <button @click="handleFavorite"
              class="flex items-center gap-2 px-3.5 py-2 rounded-lg border text-sm font-medium transition-all"
              :class="isFavorited
                ? 'bg-rose-50 border-rose-200 text-rose-600'
                : 'bg-white border-slate-200 text-slate-600 hover:border-slate-300'">
              <svg class="w-4 h-4" :class="isFavorited ? 'fill-rose-500' : ''" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"/>
              </svg>
              {{ isFavorited ? 'Saved' : 'Save' }}
            </button>
          </div>

          <!-- Rating -->
          <div v-if="userStore.isLoggedIn" class="mb-5">
            <p class="text-xs font-medium text-slate-500 mb-2 uppercase tracking-wide">Your rating</p>
            <div class="flex items-center gap-1">
              <button v-for="star in 5" :key="star"
                @click="handleRating(star)"
                class="transition-transform hover:scale-110 active:scale-95">
                <svg class="w-7 h-7 transition-colors"
                  :class="star <= thisBookRating ? 'text-amber-400 fill-amber-400' : 'text-slate-200 fill-slate-200 hover:text-amber-300 hover:fill-amber-300'"
                  viewBox="0 0 20 20">
                  <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"/>
                </svg>
              </button>
              <span v-if="thisBookRating"
                class="ml-2 text-xs text-emerald-600 font-medium flex items-center gap-1">
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7"/>
                </svg>
                Saved
              </span>
            </div>
          </div>
          <div v-else class="mb-5">
            <p class="text-xs text-slate-400">
              <router-link to="/" class="text-primary-600 hover:underline">Sign in</router-link>
              to rate this book and get personalised recommendations
            </p>
          </div>

          <!-- Description -->
          <p class="text-sm text-slate-600 leading-relaxed line-clamp-4">{{ book.description }}</p>
        </div>
      </div>
    </div>

    <!-- Similar Books -->
    <section>
      <div class="flex items-center gap-2 mb-4">
        <svg class="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/>
        </svg>
        <h2 class="text-base font-semibold text-slate-900">Similar books</h2>
        <span class="text-xs text-slate-400">· based on content similarity</span>
      </div>
      <BookGrid :books="similar" :is-loading="loadingSimilar" />
    </section>
  </div>

  <!-- Loading state -->
  <div v-else-if="loading" class="flex flex-col items-center justify-center py-24">
    <div class="w-10 h-10 border-2 border-slate-200 border-t-primary-500 rounded-full animate-spin mb-4"></div>
    <p class="text-sm text-slate-400">Loading book...</p>
  </div>

  <!-- Error state -->
  <div v-else class="flex flex-col items-center justify-center py-24 text-center">
    <div class="w-12 h-12 rounded-xl bg-slate-100 flex items-center justify-center mb-3">
      <svg class="w-6 h-6 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
      </svg>
    </div>
    <p class="text-sm font-medium text-slate-700 mb-1">Book not found</p>
    <router-link to="/" class="text-xs text-primary-600 hover:text-primary-700">Back to home</router-link>
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

const isValidUrl = computed(() => {
  const url = book.value?.image_url
  if (!url) return false
  if (url.includes('nophoto')) return false
  return url.startsWith('http')
})

const thisBookRating = computed(() =>
  userStore.ratedBooks.get(route.params.id) || 0
)

const isFavorited = computed(() =>
  userStore.favorites.has(route.params.id)
)

const genreMap = {
  'fiction': 'Fiction', 'non-fiction': 'Non-Fiction',
  'romance': 'Romance', 'fantasy, paranormal': 'Fantasy',
  'mystery, thriller, crime': 'Mystery',
  'history, historical fiction, biography': 'History',
  'children': 'Children', 'comics, graphic': 'Comics',
  'young-adult': 'Young Adult', 'poetry': 'Poetry',
  'science, technology, engineering, mathematics': 'STEM',
}

function formatGenre(g) { return genreMap[g] || g }

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
    book.value = null
  } finally {
    loading.value = false
    loadingSimilar.value = false
  }
}

async function handleFavorite() {
  await userStore.toggleFavorite(route.params.id)
}

async function handleRating(star) {
  await userStore.rateBook(route.params.id, star)
  bookStore.fetchRecommendations()
}

onMounted(() => loadBook(route.params.id))
watch(() => route.params.id, id => { if (id) loadBook(id) })
</script>

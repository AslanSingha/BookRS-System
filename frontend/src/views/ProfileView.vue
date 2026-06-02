<template>
  <div class="max-w-3xl mx-auto">

    <!-- Not logged in -->
    <div v-if="!userStore.isLoggedIn"
      class="flex flex-col items-center justify-center py-24 text-center">
      <div class="w-14 h-14 rounded-2xl bg-slate-100 flex items-center justify-center mb-4">
        <svg class="w-7 h-7 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
        </svg>
      </div>
      <h2 class="text-lg font-semibold text-slate-900 mb-1">Sign in to view your profile</h2>
      <p class="text-sm text-slate-500">Track your ratings, favorites and reading history</p>
    </div>

    <!-- Logged in -->
    <div v-else>

      <!-- Profile header -->
      <div class="bg-white border border-slate-100 rounded-2xl p-6 mb-6">
        <div class="flex items-center gap-4">
          <div class="w-14 h-14 rounded-2xl bg-primary-50 flex items-center justify-center flex-shrink-0">
            <span class="text-2xl font-bold text-primary-600">
              {{ userStore.userId.charAt(0).toUpperCase() }}
            </span>
          </div>
          <div class="flex-1">
            <h1 class="text-xl font-bold text-slate-900">{{ userStore.userId }}</h1>
            <p class="text-sm text-slate-500">
              {{ userStore.ratedBooks.size }} ratings ·
              {{ userStore.favorites.size }} favorites
            </p>
          </div>
          <!-- Recommendation mode badge -->
          <div class="text-right">
            <span class="text-xs font-medium px-2.5 py-1 rounded-lg"
              :class="recMode === 'hybrid'
                ? 'bg-primary-50 text-primary-700'
                : recMode === 'content'
                ? 'bg-emerald-50 text-emerald-700'
                : 'bg-slate-100 text-slate-600'">
              {{ recMode === 'hybrid' ? 'Hybrid AI' : recMode === 'content' ? 'Content-based' : 'Popular' }}
            </span>
            <p class="text-xs text-slate-400 mt-1">
              {{ recMode === 'hybrid'
                ? 'ALS + SBERT active'
                : recMode === 'content'
                ? `${5 - userStore.ratedBooks.size} more to unlock hybrid`
                : 'Rate 5 books to personalise' }}
            </p>
          </div>
        </div>

        <!-- Progress bar -->
        <div v-if="recMode !== 'hybrid'" class="mt-4 pt-4 border-t border-slate-100">
          <div class="flex items-center justify-between mb-1.5">
            <span class="text-xs text-slate-500">Progress to Hybrid AI</span>
            <span class="text-xs font-medium text-slate-700">
              {{ Math.min(userStore.ratedBooks.size, 5) }}/5
            </span>
          </div>
          <div class="h-1.5 bg-slate-100 rounded-full overflow-hidden">
            <div class="h-full bg-primary-500 rounded-full transition-all duration-500"
              :style="`width: ${Math.min(userStore.ratedBooks.size / 5 * 100, 100)}%`">
            </div>
          </div>
        </div>
      </div>

      <!-- Stats row -->
      <div class="grid grid-cols-3 gap-3 mb-6">
        <div class="bg-white border border-slate-100 rounded-xl p-4 text-center">
          <p class="text-2xl font-bold text-slate-900">{{ userStore.ratedBooks.size }}</p>
          <p class="text-xs text-slate-500 mt-0.5">Books rated</p>
        </div>
        <div class="bg-white border border-slate-100 rounded-xl p-4 text-center">
          <p class="text-2xl font-bold text-slate-900">{{ userStore.favorites.size }}</p>
          <p class="text-xs text-slate-500 mt-0.5">Favorites</p>
        </div>
        <div class="bg-white border border-slate-100 rounded-xl p-4 text-center">
          <p class="text-2xl font-bold text-slate-900">{{ avgRating }}</p>
          <p class="text-xs text-slate-500 mt-0.5">Avg rating</p>
        </div>
      </div>

      <!-- Favourite Genres -->
      <div v-if="topGenres.length > 0" class="bg-white border border-slate-100 rounded-xl p-4 mb-5">
        <p class="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3">Favourite Genres</p>
        <div class="flex flex-wrap gap-2">
          <div v-for="(g, i) in topGenres" :key="g.genre"
            class="flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-semibold"
            :class="i===0 ? 'bg-primary-100 text-primary-800' : i===1 ? 'bg-violet-100 text-violet-800' : 'bg-slate-100 text-slate-700'">
            <span class="font-bold opacity-50">#{{ i + 1 }}</span>
            {{ g.label }}
            <span class="opacity-60 font-normal">({{ g.count }})</span>
          </div>
        </div>
      </div>
      <!-- Tabs -->
      <div class="flex gap-1 border-b border-slate-100 mb-5">
        <button v-for="tab in tabs" :key="tab.id"
          @click="activeTab = tab.id"
          class="px-4 py-2.5 text-sm font-medium transition-colors relative"
          :class="activeTab === tab.id
            ? 'text-slate-900'
            : 'text-slate-500 hover:text-slate-700'">
          {{ tab.label }}
          <div v-if="activeTab === tab.id"
            class="absolute bottom-0 left-0 right-0 h-0.5 bg-slate-900 rounded-full">
          </div>
        </button>
      </div>

      <!-- Ratings tab -->
      <div v-if="activeTab === 'ratings'">
        <div v-if="userStore.ratedBooks.size === 0"
          class="flex flex-col items-center py-16 text-center">
          <div class="w-12 h-12 rounded-xl bg-slate-100 flex items-center justify-center mb-3">
            <svg class="w-6 h-6 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z"/>
            </svg>
          </div>
          <p class="text-sm font-medium text-slate-600">No ratings yet</p>
          <p class="text-xs text-slate-400 mt-1">Rate books to get personalised recommendations</p>
          <router-link to="/search" class="mt-4 btn-primary px-4 py-2 text-sm rounded-lg">
            Find books to rate
          </router-link>
        </div>

        <div v-else class="space-y-2">
          <router-link v-for="[bookId, rating] in userStore.ratedBooks" :key="bookId"
            :to="`/book/${bookId}`"
            class="flex items-center gap-3 p-3 bg-white border border-slate-100
              rounded-xl hover:border-slate-200 transition-all group">
            <!-- Cover -->
            <div class="w-10 h-14 bg-slate-100 rounded-lg flex-shrink-0 overflow-hidden">
              <img v-if="bookTitles[bookId]?.image_url && !imgErrors[bookId]"
                :src="bookTitles[bookId].image_url"
                class="w-full h-full object-cover"
                @error="imgErrors[bookId] = true" />
              <div v-else class="w-full h-full flex items-center justify-center">
                <svg class="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
                </svg>
              </div>
            </div>
            <!-- Info -->
            <div class="flex-1 min-w-0">
              <p class="text-sm font-medium text-slate-900 truncate
                group-hover:text-primary-600 transition-colors">
                {{ bookTitles[bookId]?.title || 'Loading...' }}
              </p>
              <p class="text-xs text-slate-400 truncate">
                {{ bookTitles[bookId]?.authors || '' }}
              </p>
            </div>
            <!-- Stars -->
            <div class="flex items-center gap-0.5 flex-shrink-0">
              <svg v-for="star in 5" :key="star"
                class="w-3.5 h-3.5"
                :class="star <= rating ? 'text-amber-400 fill-amber-400' : 'text-slate-200 fill-slate-200'"
                viewBox="0 0 20 20">
                <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"/>
              </svg>
            </div>
          </router-link>
        </div>
      </div>

      <!-- Favorites tab -->
      <div v-if="activeTab === 'favorites'">
        <div v-if="userStore.favorites.size === 0"
          class="flex flex-col items-center py-16 text-center">
          <div class="w-12 h-12 rounded-xl bg-slate-100 flex items-center justify-center mb-3">
            <svg class="w-6 h-6 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"/>
            </svg>
          </div>
          <p class="text-sm font-medium text-slate-600">No favorites yet</p>
          <p class="text-xs text-slate-400 mt-1">Save books you love to find them later</p>
        </div>

        <div v-else class="space-y-2">
          <router-link v-for="bookId in userStore.favorites" :key="bookId"
            :to="`/book/${bookId}`"
            class="flex items-center gap-3 p-3 bg-white border border-slate-100
              rounded-xl hover:border-slate-200 transition-all group">
            <div class="w-10 h-14 bg-slate-100 rounded-lg flex-shrink-0 overflow-hidden">
              <img v-if="bookTitles[bookId]?.image_url && !imgErrors[bookId]"
                :src="bookTitles[bookId].image_url"
                class="w-full h-full object-cover"
                @error="imgErrors[bookId] = true" />
              <div v-else class="w-full h-full flex items-center justify-center">
                <svg class="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
                </svg>
              </div>
            </div>
            <div class="flex-1 min-w-0">
              <p class="text-sm font-medium text-slate-900 truncate
                group-hover:text-primary-600 transition-colors">
                {{ bookTitles[bookId]?.title || 'Loading...' }}
              </p>
              <p class="text-xs text-slate-400 truncate">
                {{ bookTitles[bookId]?.authors || '' }}
              </p>
            </div>
            <svg class="w-4 h-4 text-rose-400 fill-rose-400 flex-shrink-0" viewBox="0 0 24 24">
              <path d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"/>
            </svg>
          </router-link>
        </div>
      </div>

      <!-- Activity tab -->
      <div v-if="activeTab === 'activity'">
        <div v-if="actions.length === 0"
          class="flex flex-col items-center py-16 text-center">
          <div class="w-12 h-12 rounded-xl bg-slate-100 flex items-center justify-center mb-3">
            <svg class="w-6 h-6 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
          </div>
          <p class="text-sm font-medium text-slate-600">No activity yet</p>
        </div>

        <div v-else class="space-y-2">
          <div v-for="action in actions.slice(0, 50)" :key="action.id"
            class="flex items-center gap-3 p-3 bg-white border border-slate-100 rounded-xl">
            <!-- Action icon -->
            <div class="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
              :class="actionBg(action.action_type)">
              <svg class="w-4 h-4" :class="actionColor(action.action_type)"
                fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  :d="actionIcon(action.action_type)"/>
              </svg>
            </div>
            <div class="flex-1 min-w-0">
              <p class="text-sm text-slate-700 truncate">
                <span class="font-medium">{{ actionLabel(action.action_type) }}</span>
                {{ bookTitles[action.book_id]?.title || action.book_id }}
              </p>
              <p class="text-xs text-slate-400">
                {{ formatDate(action.created_at) }}
              </p>
            </div>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useUserStore } from '../stores/user'
import { booksApi, actionsApi } from '../services/api'

const userStore = useUserStore()
const activeTab = ref('ratings')
const bookTitles = ref({})
const imgErrors = ref({})
const actions = ref([])

const tabs = computed(() => [
  { id: 'ratings', label: `Ratings (${userStore.ratedBooks.size})` },
  { id: 'favorites', label: `Favorites (${userStore.favorites.size})` },
  { id: 'activity', label: 'Activity' },
])

const recMode = computed(() => {
  if (userStore.ratedBooks.size >= 5) return 'hybrid'
  if (userStore.ratedBooks.size > 0) return 'content'
  return 'popular'
})

const avgRating = computed(() => {
  if (userStore.ratedBooks.size === 0) return '—'
  const ratings = [...userStore.ratedBooks.values()]
  return (ratings.reduce((a, b) => a + b, 0) / ratings.length).toFixed(1)
})

const topGenres = computed(() => {
  const genreCount = {}
  for (const [bookId] of userStore.ratedBooks) {
    const book = bookTitles.value[bookId]
    if (book && book.genre) {
      genreCount[book.genre] = (genreCount[book.genre] || 0) + 1
    }
  }
  const labels = {
    'fiction':                                       'Fiction',
    'non-fiction':                                   'Non-Fiction',
    'romance':                                       'Romance',
    'fantasy, paranormal':                           'Fantasy',
    'mystery, thriller, crime':                      'Mystery',
    'history, historical fiction, biography':        'History',
    'children':                                      'Children',
    'comics, graphic':                               'Comics',
    'young-adult':                                   'Young Adult',
    'poetry':                                        'Poetry',
    'science, technology, engineering, mathematics': 'STEM',
  }
  return Object.entries(genreCount)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3)
    .map(([genre, count]) => ({
      genre, count,
      label: labels[genre] || genre,
    }))
})
function actionIcon(type) {
  const map = {
    view: 'M15 12a3 3 0 11-6 0 3 3 0 016 0z M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z',
    favorite: 'M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z',
    rating: 'M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z',
    search_click: 'M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0',
  }
  return map[type] || 'M5 12h14'
}

function actionBg(type) {
  const map = { view: 'bg-slate-50', favorite: 'bg-rose-50', rating: 'bg-amber-50', search_click: 'bg-primary-50' }
  return map[type] || 'bg-slate-50'
}

function actionColor(type) {
  const map = { view: 'text-slate-500', favorite: 'text-rose-500', rating: 'text-amber-500', search_click: 'text-primary-500' }
  return map[type] || 'text-slate-500'
}

function actionLabel(type) {
  const map = { view: 'Viewed', favorite: 'Saved', rating: 'Rated', search_click: 'Searched' }
  return map[type] || type
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

async function loadBookTitles(bookIds) {
  const missing = bookIds.filter(id => !bookTitles.value[id])
  await Promise.all(missing.map(async (id) => {
    try {
      const res = await booksApi.getBook(id)
      bookTitles.value[id] = res.data
    } catch {
      bookTitles.value[id] = { title: `Book ${id}`, authors: '' }
    }
  }))
}

onMounted(async () => {
  if (!userStore.isLoggedIn) return
  try {
    const res = await actionsApi.getUserActions(userStore.userId)
    actions.value = res.data
  } catch (e) {
    console.error('Failed to load actions:', e)
  }
  const allBookIds = [
    ...userStore.ratedBooks.keys(),
    ...userStore.favorites,
    ...actions.value.map(a => a.book_id)
  ]
  await loadBookTitles([...new Set(allBookIds)])
})
</script>

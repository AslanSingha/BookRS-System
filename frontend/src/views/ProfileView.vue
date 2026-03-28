<template>
  <div class="max-w-4xl mx-auto">
    <div v-if="!userStore.isLoggedIn" class="text-center py-16">
      <p class="text-5xl mb-4">👤</p>
      <p class="text-xl font-semibold mb-2">You are not logged in</p>
      <p class="text-gray-500 mb-6">Login to track your favorites, ratings and history</p>
    </div>

    <div v-else>
      <!-- Header -->
      <div class="card mb-6">
        <div class="flex items-center gap-4">
          <div class="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center text-3xl">👤</div>
          <div>
            <h1 class="text-2xl font-bold">{{ userStore.userId }}</h1>
            <p class="text-gray-500 text-sm">BookRS Member</p>
          </div>
          <div class="ml-auto grid grid-cols-3 gap-6 text-center">
            <div>
              <p class="text-2xl font-bold text-primary-600">{{ userStore.ratedBooks.size }}</p>
              <p class="text-xs text-gray-500">Ratings</p>
            </div>
            <div>
              <p class="text-2xl font-bold text-red-500">{{ userStore.favorites.size }}</p>
              <p class="text-xs text-gray-500">Favorites</p>
            </div>
            <div>
              <p class="text-2xl font-bold"
                :class="{
                  'text-orange-500': recommendMode === 'Popular',
                  'text-blue-500': recommendMode === 'Content',
                  'text-green-600': recommendMode === 'Hybrid',
                }">
                {{ recommendMode }}
              </p>
              <p class="text-xs text-gray-500">Mode</p>
            </div>
          </div>
        </div>

        <!-- Progress bar -->
        <div class="mt-4">
          <div class="flex justify-between text-xs text-gray-500 mb-1">
            <span>Personalization progress</span>
            <span>{{ userStore.ratedBooks.size }}/5 ratings for full hybrid</span>
          </div>
          <div class="w-full bg-gray-100 rounded-full h-2">
            <div class="h-2 rounded-full transition-all"
              :class="{
                'bg-orange-400': userStore.ratedBooks.size === 0,
                'bg-blue-500': userStore.ratedBooks.size > 0 && userStore.ratedBooks.size < 5,
                'bg-green-500': userStore.ratedBooks.size >= 5,
              }"
              :style="{ width: Math.min(100, userStore.ratedBooks.size * 20) + '%' }">
            </div>
          </div>
          <p class="text-xs mt-1"
            :class="{
              'text-orange-600': userStore.ratedBooks.size === 0,
              'text-blue-600': userStore.ratedBooks.size > 0 && userStore.ratedBooks.size < 5,
              'text-green-600': userStore.ratedBooks.size >= 5,
            }">
            {{ stageMessage }}
          </p>
        </div>
      </div>

      <!-- Tabs -->
      <div class="flex gap-2 mb-6">
        <button v-for="tab in tabs" :key="tab.id"
          @click="activeTab = tab.id"
          :class="[
            'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
            activeTab === tab.id
              ? 'bg-primary-600 text-white'
              : 'bg-white text-gray-600 border border-gray-200 hover:border-primary-400'
          ]">
          {{ tab.label }}
        </button>
      </div>

      <!-- Rated Books -->
      <div v-if="activeTab === 'ratings'">
        <div v-if="userStore.ratedBooks.size === 0" class="text-center py-12 text-gray-400">
          <p class="text-4xl mb-3">⭐</p>
          <p>No ratings yet — rate books to get personalized recommendations!</p>
        </div>
        <div v-else class="grid grid-cols-1 gap-3">
          <router-link v-for="[bookId, rating] in userStore.ratedBooks" :key="bookId"
            :to="`/book/${bookId}`"
            class="card flex items-center gap-4 hover:shadow-md transition-shadow">
            <!-- Book cover mini -->
            <div class="w-12 h-16 bg-primary-50 rounded flex items-center justify-center flex-shrink-0 overflow-hidden">
              <img v-if="bookTitles[bookId]?.image_url"
                :src="bookTitles[bookId].image_url"
                class="w-full h-full object-cover"
                @error="(e) => e.target.style.display='none'" />
              <span v-else class="text-xl">📖</span>
            </div>
            <div class="flex-1 min-w-0">
              <p class="font-medium text-gray-900 truncate">
                {{ bookTitles[bookId]?.title || 'Loading...' }}
              </p>
              <p class="text-xs text-gray-500 truncate">
                {{ bookTitles[bookId]?.authors || '' }}
              </p>
            </div>
            <div class="flex gap-0.5 flex-shrink-0">
              <span v-for="star in 5" :key="star"
                class="text-sm"
                :class="star <= rating ? 'text-yellow-400' : 'text-gray-200'">★</span>
            </div>
            <span class="text-sm font-medium text-gray-500 flex-shrink-0">{{ rating }}/5</span>
          </router-link>
        </div>
      </div>

      <!-- Favorites -->
      <div v-if="activeTab === 'favorites'">
        <div v-if="userStore.favorites.size === 0" class="text-center py-12 text-gray-400">
          <p class="text-4xl mb-3">❤️</p>
          <p>No favorites yet — heart books you love!</p>
        </div>
        <div v-else class="grid grid-cols-1 gap-3">
          <div v-for="bookId in userStore.favorites" :key="bookId"
            class="card flex items-center gap-4">
            <div class="w-12 h-16 bg-primary-50 rounded flex items-center justify-center flex-shrink-0 overflow-hidden">
              <img v-if="bookTitles[bookId]?.image_url"
                :src="bookTitles[bookId].image_url"
                class="w-full h-full object-cover"
                @error="(e) => e.target.style.display='none'" />
              <span v-else class="text-2xl">📖</span>
            </div>
            <div class="flex-1 min-w-0">
              <router-link :to="`/book/${bookId}`"
                class="font-medium text-primary-600 hover:underline block truncate">
                {{ bookTitles[bookId]?.title || 'Loading...' }}
              </router-link>
              <p class="text-xs text-gray-500 truncate">{{ bookTitles[bookId]?.authors || '' }}</p>
            </div>
            <span class="text-red-400 text-xl">❤️</span>
            <button @click="userStore.toggleFavorite(bookId)"
              class="text-xs text-gray-400 hover:text-red-500 flex-shrink-0">Remove</button>
          </div>
        </div>
      </div>

      <!-- Activity History -->
      <div v-if="activeTab === 'history'">
        <div v-if="actions.length === 0" class="text-center py-12 text-gray-400">
          <p class="text-4xl mb-3">📋</p>
          <p>No activity yet — start exploring books!</p>
        </div>
        <div v-else class="grid grid-cols-1 gap-2">
          <div v-for="action in actions" :key="action.id"
            class="card flex items-center gap-3 text-sm py-3">
            <span class="text-lg flex-shrink-0">{{ actionIcon(action.action_type) }}</span>
            <span class="text-gray-500 capitalize flex-shrink-0 w-20">{{ action.action_type }}</span>
            <router-link :to="`/book/${action.book_id}`"
              class="text-primary-600 hover:underline flex-1 truncate">
              {{ bookTitles[action.book_id]?.title || action.book_id }}
            </router-link>
            <span v-if="action.value > 0 && action.action_type === 'rating'"
              class="text-yellow-500 flex-shrink-0">{{ action.value }}★</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useUserStore } from '../stores/user'
import { actionsApi, booksApi } from '../services/api'

const userStore = useUserStore()
const activeTab = ref('ratings')
const actions = ref([])
const bookTitles = ref({})

const tabs = computed(() => [
  { id: 'ratings', label: `⭐ Ratings (${userStore.ratedBooks.size})` },
  { id: 'favorites', label: `❤️ Favorites (${userStore.favorites.size})` },
  { id: 'history', label: `📋 Activity (${actions.value.length})` },
])

const recommendMode = computed(() => {
  const n = userStore.ratedBooks.size
  if (n === 0) return 'Popular'
  if (n < 5) return 'Content'
  return 'Hybrid'
})

const stageMessage = computed(() => {
  const n = userStore.ratedBooks.size
  if (n === 0) return 'Rate books to start personalizing your recommendations'
  if (n < 5) return `Rate ${5 - n} more books to unlock full Hybrid AI recommendations!`
  return 'Full hybrid recommendations active (ALS + SBERT)'
})

function actionIcon(type) {
  const map = { view: '👁️', favorite: '❤️', rating: '⭐', search_click: '🔍' }
  return map[type] || '📌'
}

async function loadBookTitles(bookIds) {
  const missing = bookIds.filter(id => !bookTitles.value[id])
  await Promise.all(missing.map(async (id) => {
    try {
      const res = await booksApi.getBook(id)
      bookTitles.value[id] = res.data
    } catch (e) {
      bookTitles.value[id] = { title: `Book ${id}`, authors: '' }
    }
  }))
}

onMounted(async () => {
  if (!userStore.isLoggedIn) return

  // Load activity history
  try {
    const res = await actionsApi.getUserActions(userStore.userId)
    actions.value = res.data
  } catch (e) {
    console.error('Failed to load actions:', e)
  }

  // Load book titles for all known books
  const allBookIds = [
    ...userStore.ratedBooks.keys(),
    ...userStore.favorites,
    ...actions.value.map(a => a.book_id)
  ]
  await loadBookTitles([...new Set(allBookIds)])
})
</script>

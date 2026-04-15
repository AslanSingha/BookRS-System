<template>
  <div>
    <h1 class="text-2xl font-bold mb-6">🔍 Search Books</h1>

    <!-- Search bar -->
    <form @submit.prevent="handleSearch" class="mb-6">
      <div class="flex gap-3">
        <input
          v-model="query"
          type="text"
          placeholder="Search by title, author, topic, genre..."
          class="flex-1 px-4 py-3 rounded-xl border border-gray-200 focus:outline-none focus:border-primary-500 focus:ring-1 focus:ring-primary-500"
        />
        <button type="submit" class="btn-primary px-6 py-3 rounded-xl">Search</button>
      </div>
    </form>

    <!-- Tabs -->
    <div v-if="lastQuery" class="flex gap-2 mb-6">
      <button
        @click="activeTab = 'semantic'"
        :class="[
          'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
          activeTab === 'semantic'
            ? 'bg-primary-600 text-white'
            : 'bg-white text-gray-600 border border-gray-200 hover:border-primary-400'
        ]">
        🔍 Semantic Search
        <span class="text-xs ml-1 opacity-75">SBERT only</span>
      </button>
      <button
        @click="activeTab = 'personalized'"
        :class="[
          'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
          activeTab === 'personalized'
            ? 'bg-primary-600 text-white'
            : 'bg-white text-gray-600 border border-gray-200 hover:border-primary-400'
        ]">
        ✨ For You
        <span class="text-xs ml-1 opacity-75">SBERT + ALS</span>
      </button>
    </div>

    <!-- Results -->
    <div v-if="lastQuery">
      <div class="flex items-center justify-between mb-4">
        <h2 class="font-semibold text-gray-700">
          {{ currentResults.length }} results for "{{ lastQuery }}"
        </h2>
        <span class="text-sm text-gray-400">
          {{ activeTab === 'semantic' ? 'Semantic search powered by SBERT' : 'Personalized by SBERT + ALS' }}
        </span>
      </div>

      <!-- Not logged in warning for personalized tab -->
      <div v-if="activeTab === 'personalized' && !userStore.isLoggedIn"
        class="bg-yellow-50 border border-yellow-200 rounded-xl p-3 mb-4 text-sm text-yellow-700">
        💡 Login and rate books to get personalized search results!
        Showing semantic search results instead.
      </div>

      <BookGrid :books="currentResults" :is-loading="isLoading" />
    </div>

    <!-- Empty state -->
    <div v-else class="text-center py-16 text-gray-400">
      <p class="text-5xl mb-4">🔍</p>
      <p class="text-lg">Search for any book, author, or topic</p>
      <p class="text-sm mt-2">
        BookRS uses semantic search to find what you mean, not just what you type
      </p>
      <div class="mt-4 flex justify-center gap-4 text-sm">
        <span class="bg-gray-100 px-3 py-1 rounded-full">🔍 Semantic Search</span>
        <span class="bg-primary-50 text-primary-700 px-3 py-1 rounded-full">✨ Personalized For You</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useBookStore } from '../stores/books'
import { useUserStore } from '../stores/user'
import { searchApi, recommendApi } from '../services/api'
import BookGrid from '../components/BookGrid.vue'

const store = useBookStore()
const userStore = useUserStore()
const route = useRoute()
const router = useRouter()
const query = ref('')
const lastQuery = ref('')
const activeTab = ref('semantic')
const isLoading = ref(false)
const semanticResults = ref([])
const personalizedResults = ref([])

const currentResults = computed(() =>
  activeTab.value === 'semantic' ? semanticResults.value : personalizedResults.value
)

async function handleSearch() {
  if (!query.value.trim()) return
  lastQuery.value = query.value
  router.replace({ name: 'Search', query: { q: query.value } })
  await Promise.all([
    doSemanticSearch(query.value),
    doPersonalizedSearch(query.value)
  ])
}

async function doSemanticSearch(q) {
  isLoading.value = true
  try {
    const res = await searchApi.search(q, 20)
    semanticResults.value = res.data.results
  } catch (e) {
    console.error('Semantic search failed:', e)
  } finally {
    isLoading.value = false
  }
}

async function doPersonalizedSearch(q) {
  if (!userStore.isLoggedIn) {
    personalizedResults.value = semanticResults.value
    return
  }
  try {
    const ratedBooks = [...userStore.ratedBooks.keys()].join(',')
    const res = await searchApi.personalized(
      q, userStore.userId, 20, ratedBooks
    )
    personalizedResults.value = res.data.results
  } catch (e) {
    console.error('Personalized search failed:', e)
    personalizedResults.value = semanticResults.value
  }
}

watch(() => route.query.q, (newQ) => {
  if (newQ && newQ !== lastQuery.value) {
    query.value = newQ
    lastQuery.value = newQ
    doSemanticSearch(newQ)
    doPersonalizedSearch(newQ)
  }
}, { immediate: true })

onMounted(() => {
  if (route.query.q) {
    query.value = route.query.q
    lastQuery.value = route.query.q
    doSemanticSearch(route.query.q)
    doPersonalizedSearch(route.query.q)
  }
})
</script>

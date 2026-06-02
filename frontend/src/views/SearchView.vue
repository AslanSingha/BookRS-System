<template>
  <div>
    <!-- Header — shows current query or default -->
    <div class="mb-6">
      <div class="flex items-center gap-2 mb-1">
        <svg class="w-5 h-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0"/>
        </svg>
        <h1 class="text-2xl font-bold text-slate-900">
          {{ lastQuery ? `"${lastQuery}"` : 'Search' }}
        </h1>
      </div>
      <p class="text-sm text-slate-500">
        {{ lastQuery
          ? 'Use the search bar above to refine your query'
          : 'Use the search bar above to find books by title, author or topic' }}
      </p>
    </div>

    <!-- Results -->
    <div v-if="lastQuery">
      <!-- Tabs -->
      <div class="flex items-center gap-1 mb-5 border-b border-slate-100 pb-0">
        <button @click="activeTab = 'semantic'"
          class="px-4 py-2.5 text-sm font-medium transition-colors relative"
          :class="activeTab === 'semantic'
            ? 'text-slate-900'
            : 'text-slate-500 hover:text-slate-700'">
          <span class="flex items-center gap-2">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0"/>
            </svg>
            Semantic
          </span>
          <div v-if="activeTab === 'semantic'"
            class="absolute bottom-0 left-0 right-0 h-0.5 bg-slate-900 rounded-full"></div>
        </button>
        <button @click="activeTab = 'personalized'"
          class="px-4 py-2.5 text-sm font-medium transition-colors relative"
          :class="activeTab === 'personalized'
            ? 'text-slate-900'
            : 'text-slate-500 hover:text-slate-700'">
          <span class="flex items-center gap-2">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"/>
            </svg>
            For You
            <span v-if="!userStore.isLoggedIn"
              class="text-xs bg-slate-100 text-slate-500 px-1.5 py-0.5 rounded">
              Sign in
            </span>
          </span>
          <div v-if="activeTab === 'personalized'"
            class="absolute bottom-0 left-0 right-0 h-0.5 bg-slate-900 rounded-full"></div>
        </button>
      </div>

      <!-- Result count -->
      <div class="flex items-center justify-between mb-4">
        <p class="text-sm text-slate-500">
          <span class="font-medium text-slate-900">{{ currentResults.length }}</span>
          results for
          <span class="font-medium text-slate-900">"{{ lastQuery }}"</span>
        </p>
        <p class="text-xs text-slate-400">
          {{ activeTab === 'semantic' ? 'SBERT semantic search' : 'Personalised · SBERT + ALS' }}
        </p>
      </div>

      <!-- Not logged in warning -->
      <div v-if="activeTab === 'personalized' && !userStore.isLoggedIn"
        class="bg-primary-50 border border-primary-100 rounded-xl p-3 mb-4 flex items-center gap-3">
        <svg class="w-4 h-4 text-primary-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
        </svg>
        <p class="text-xs text-primary-700">
          Sign in and rate books to get results personalised to your taste.
          Showing semantic results instead.
        </p>
      </div>

      <BookGrid :books="currentResults" :is-loading="isLoading" :onCardClick="handleSearchClick" />
    </div>

    <!-- Empty state -->
    <div v-else class="flex flex-col items-center justify-center py-20 text-center">
      <div class="w-14 h-14 rounded-2xl bg-slate-100 flex items-center justify-center mb-4">
        <svg class="w-7 h-7 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0"/>
        </svg>
      </div>
      <h3 class="text-base font-semibold text-slate-700 mb-1">Search for any book</h3>
      <p class="text-sm text-slate-400 max-w-sm">
        BookRS uses semantic search — search by meaning, not just keywords.
        Try "dystopian society", "magical realism", or an author name.
      </p>
      <div class="flex flex-wrap gap-2 justify-center mt-5">
        <button v-for="hint in hints" :key="hint"
          @click="router.push({ name: 'Search', query: { q: hint } })"
          class="text-xs px-3 py-1.5 rounded-lg bg-slate-100 text-slate-600 hover:bg-slate-200 transition-colors">
          {{ hint }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { useBookStore } from '../stores/books'
import { useUserStore } from '../stores/user'
import { searchApi } from '../services/api'
import BookGrid from '../components/BookGrid.vue'

const store = useBookStore()
const userStore = useUserStore()
const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

async function handleSearchClick(bookId) {
  await userStore.logSearchClick(bookId)
}
const query = ref('')
const lastQuery = ref('')
const activeTab = ref('semantic')
const isLoading = ref(false)
const semanticResults = ref([])
const personalizedResults = ref([])

const hints = ['magic adventure', 'dystopian society', 'self improvement', 'historical fiction', 'mystery thriller', 'STEM science']

const currentResults = computed(() =>
  activeTab.value === 'semantic' ? semanticResults.value : personalizedResults.value
)

async function handleSearch() {
  if (!query.value.trim()) return
  lastQuery.value = query.value
  router.replace({ name: 'Search', query: { q: query.value } })
  isLoading.value = true
  try {
    const [semRes] = await Promise.all([
      searchApi.search(query.value, 20),
    ])
    semanticResults.value = semRes.data.results
    if (userStore.isLoggedIn) {
      const ratedBooks = [...userStore.ratedBooks.keys()].join(',')
      const perRes = await searchApi.personalized(query.value, userStore.userId, 30, ratedBooks)
      personalizedResults.value = perRes.data.results
    } else {
      personalizedResults.value = semanticResults.value
    }
  } catch (e) {
    console.error('Search failed:', e)
  } finally {
    isLoading.value = false
  }
}

watch(() => route.query.q, (newQ) => {
  if (newQ && newQ !== lastQuery.value) {
    query.value = newQ
    handleSearch()
  }
}, { immediate: true })

onMounted(() => {
  if (route.query.q) {
    query.value = route.query.q
    handleSearch()
  }
})
</script>

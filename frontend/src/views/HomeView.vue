<template>
  <div>
    <!-- Hero -->
    <div class="bg-gradient-to-r from-primary-700 to-primary-500 rounded-2xl p-8 mb-8 text-white">
      <h1 class="text-3xl font-bold mb-2">Welcome to BookRS 📚</h1>
      <p class="text-primary-100 mb-4">AI-powered book recommendations just for you</p>
      <router-link to="/search" class="bg-white text-primary-700 px-6 py-2 rounded-full font-semibold hover:bg-primary-50 transition-colors inline-block">
        Discover Books
      </router-link>
    </div>

    <!-- Recommendation method badge -->
    <section class="mb-10">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-xl font-bold text-gray-900">✨ Recommended For You</h2>
        <div class="flex items-center gap-2">
          <span class="text-xs px-3 py-1 rounded-full font-medium"
            :class="{
              'bg-blue-50 text-blue-700': store.recommendMethod === 'hybrid',
              'bg-green-50 text-green-700': store.recommendMethod === 'content',
              'bg-orange-50 text-orange-700': store.recommendMethod === 'popular',
            }">
            {{ methodLabel }}
          </span>
          <button @click="store.fetchRecommendations()"
            class="text-xs text-gray-400 hover:text-primary-600">
            🔄 Refresh
          </button>
        </div>
      </div>

      <!-- Cold start hint -->
      <div v-if="store.recommendMethod === 'popular' && userStore.isLoggedIn"
        class="bg-blue-50 border border-blue-100 rounded-xl p-3 mb-4 text-sm text-blue-700">
        💡 Rate some books to get personalized recommendations!
        <span class="font-medium">{{ userStore.ratedBooks.size }}/5 ratings done</span>
      </div>

      <BookGrid :books="store.recommendations" :is-loading="store.isLoading" />
    </section>

    <!-- Trending -->
    <section class="mb-10">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-xl font-bold text-gray-900">📈 Trending Now</h2>
        <router-link to="/trending" class="text-sm text-primary-600 hover:underline">See all</router-link>
      </div>
      <BookGrid :books="store.trending.slice(0, 6)" :is-loading="store.isLoading" />
    </section>

    <!-- Popular -->
    <section class="mb-10">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-xl font-bold text-gray-900">🔥 Most Popular</h2>
        <router-link to="/popular" class="text-sm text-primary-600 hover:underline">See all</router-link>
      </div>
      <BookGrid :books="store.popular.slice(0, 6)" :is-loading="store.isLoading" />
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useBookStore } from '../stores/books'
import { useUserStore } from '../stores/user'
import BookGrid from '../components/BookGrid.vue'

const store = useBookStore()
const userStore = useUserStore()

const methodLabel = computed(() => {
  const map = {
    'hybrid': '🤖 Hybrid (ALS + SBERT)',
    'content': '📖 Content-Based (SBERT)',
    'popular': '🔥 Popular Books',
  }
  return map[store.recommendMethod] || store.recommendMethod
})

onMounted(async () => {
  await Promise.all([
    store.fetchRecommendations(),
    store.fetchTrending(),
    store.fetchPopular(),
  ])
})
</script>

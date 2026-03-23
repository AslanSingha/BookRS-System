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

    <!-- Recommended for you -->
    <section class="mb-10">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-xl font-bold text-gray-900">✨ Recommended For You</h2>
        <span class="text-sm text-gray-400">Powered by BookRS Hybrid (ALS + SBERT)</span>
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
import { onMounted } from 'vue'
import { useBookStore } from '../stores/books'
import BookGrid from '../components/BookGrid.vue'

const store = useBookStore()

onMounted(async () => {
  await Promise.all([
    store.fetchRecommendations(),
    store.fetchTrending(),
    store.fetchPopular(),
  ])
})
</script>

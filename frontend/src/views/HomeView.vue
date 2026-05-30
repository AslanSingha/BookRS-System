<template>
  <div>

    <!-- NOT LOGGED IN VIEW -->
    <template v-if="!userStore.isLoggedIn">

      <!-- Hero -->
      <div class="bg-gradient-to-r from-primary-700 to-primary-500 rounded-2xl p-8 mb-8 text-white">
        <h1 class="text-3xl font-bold mb-2">Welcome to BookRS 📚</h1>
        <p class="text-primary-100 mb-2">
          AI-powered book recommendations personalised just for you.
        </p>
        <p class="text-primary-200 text-sm mb-5">
          Login and rate a few books to unlock hybrid recommendations powered by ALS + SBERT.
        </p>
        <div class="flex gap-3">
          <router-link to="/search"
            class="bg-white text-primary-700 px-6 py-2 rounded-full font-semibold hover:bg-primary-50 transition-colors inline-block text-sm">
            Browse Books
          </router-link>
        </div>
      </div>

      <!-- Trending -->
      <section class="mb-10">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-xl font-bold text-gray-900">📈 Trending Now</h2>
          <router-link to="/trending" class="text-sm text-primary-600 hover:underline">See all</router-link>
        </div>
        <BookGrid :books="store.trending.slice(0, 6)" :is-loading="store.isLoading" />
      </section>

      <!-- Most Popular -->
      <section class="mb-10">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-xl font-bold text-gray-900">🔥 Most Popular</h2>
          <router-link to="/popular" class="text-sm text-primary-600 hover:underline">See all</router-link>
        </div>
        <BookGrid :books="store.popular.slice(0, 6)" :is-loading="store.isLoading" />
      </section>

      <!-- Login CTA -->
      <div class="bg-gray-50 border border-gray-200 rounded-2xl p-8 text-center mb-10">
        <p class="text-3xl mb-3">🤖</p>
        <h3 class="text-xl font-bold text-gray-900 mb-2">
          Get Personalised Recommendations
        </h3>
        <p class="text-gray-500 text-sm mb-4">
          Login and rate 5 books to unlock full hybrid recommendations
          powered by ALS collaborative filtering and SBERT semantic embeddings.
        </p>
        <div class="flex justify-center gap-3">
          <div class="flex items-center gap-2 text-sm text-gray-400">
            <span class="w-2 h-2 rounded-full bg-orange-400"></span> 0 ratings → Popular
          </div>
          <div class="flex items-center gap-2 text-sm text-gray-400">
            <span class="w-2 h-2 rounded-full bg-green-400"></span> 1–4 ratings → Content-Based
          </div>
          <div class="flex items-center gap-2 text-sm text-gray-400">
            <span class="w-2 h-2 rounded-full bg-blue-400"></span> 5+ ratings → Hybrid AI
          </div>
        </div>
      </div>

    </template>

    <!-- LOGGED IN VIEW -->
    <template v-else>

      <!-- Onboarding banner for 0 ratings -->
      <div v-if="userStore.ratedBooks.size === 0"
        class="bg-gradient-to-r from-blue-600 to-primary-600 rounded-2xl p-6 mb-6 text-white">
        <div class="flex items-center justify-between">
          <div>
            <h2 class="text-xl font-bold mb-1">👋 Welcome, {{ userStore.userId }}!</h2>
            <p class="text-blue-100 text-sm mb-3">
              Rate at least 5 books to unlock personalised hybrid recommendations.
            </p>
            <div class="flex items-center gap-3">
              <div class="flex gap-1">
                <div v-for="i in 5" :key="i"
                  class="w-6 h-2 rounded-full"
                  :class="i <= userStore.ratedBooks.size ? 'bg-white' : 'bg-white/30'">
                </div>
              </div>
              <span class="text-xs text-blue-100">
                {{ userStore.ratedBooks.size }}/5 ratings
              </span>
            </div>
          </div>
          <router-link to="/search"
            class="bg-white text-primary-700 px-5 py-2 rounded-full font-semibold hover:bg-blue-50 transition-colors text-sm flex-shrink-0">
            Rate Books →
          </router-link>
        </div>
      </div>

      <!-- Active mode banner for 1-4 ratings -->
      <div v-else-if="userStore.ratedBooks.size < 5"
        class="bg-gradient-to-r from-green-600 to-green-500 rounded-2xl p-5 mb-6 text-white">
        <div class="flex items-center justify-between">
          <div>
            <h2 class="text-lg font-bold mb-1">📖 Content-Based Recommendations Active</h2>
            <p class="text-green-100 text-sm">
              Rate {{ 5 - userStore.ratedBooks.size }} more books to unlock
              full Hybrid AI (ALS + SBERT).
            </p>
          </div>
          <div class="flex gap-1 flex-shrink-0">
            <div v-for="i in 5" :key="i"
              class="w-5 h-2 rounded-full"
              :class="i <= userStore.ratedBooks.size ? 'bg-white' : 'bg-white/30'">
            </div>
          </div>
        </div>
      </div>

      <!-- Hybrid active banner for 5+ ratings -->
      <div v-else
        class="bg-gradient-to-r from-primary-700 to-primary-500 rounded-2xl p-5 mb-6 text-white">
        <div class="flex items-center justify-between">
          <div>
            <h2 class="text-lg font-bold mb-1">🤖 Hybrid AI Recommendations Active</h2>
            <p class="text-primary-100 text-sm">
              Personalised using ALS collaborative filtering + SBERT semantic embeddings.
            </p>
          </div>
          <span class="text-3xl flex-shrink-0">🎯</span>
        </div>
      </div>

      <!-- Recommended For You -->
      <section class="mb-10">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-xl font-bold text-gray-900">✨ Recommended For You</h2>
          <div class="flex items-center gap-2">
            <span class="text-xs px-3 py-1 rounded-full font-medium"
              :class="{
                'bg-blue-50 text-blue-700':     actualMethod === 'hybrid',
                'bg-green-50 text-green-700':   actualMethod === 'content',
                'bg-orange-50 text-orange-700': actualMethod === 'popular',
              }">
              {{ methodLabel }}
            </span>
            <button @click="store.fetchRecommendations()"
              class="text-xs text-gray-400 hover:text-primary-600">
              🔄 Refresh
            </button>
          </div>
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

      <!-- Most Popular -->
      <section class="mb-10">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-xl font-bold text-gray-900">🔥 Most Popular</h2>
          <router-link to="/popular" class="text-sm text-primary-600 hover:underline">See all</router-link>
        </div>
        <BookGrid :books="store.popular.slice(0, 6)" :is-loading="store.isLoading" />
      </section>

    </template>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useBookStore } from '../stores/books'
import { useUserStore } from '../stores/user'
import BookGrid from '../components/BookGrid.vue'

const store = useBookStore()
const userStore = useUserStore()

const actualMethod = computed(() => {
  if (!userStore.isLoggedIn) return 'popular'
  if (userStore.ratedBooks.size === 0) return 'popular'
  if (userStore.ratedBooks.size < 5) return 'content'
  return 'hybrid'
})

const methodLabel = computed(() => {
  const map = {
    'hybrid':  '🤖 Hybrid (ALS + SBERT)',
    'content': '📖 Content-Based (SBERT)',
    'popular': '🔥 Popular Books',
  }
  return map[actualMethod.value] || actualMethod.value
})

onMounted(async () => {
  await Promise.all([
    store.fetchRecommendations(),
    store.fetchTrending(),
    store.fetchPopular(),
  ])
})
</script>

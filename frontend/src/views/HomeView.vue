<template>
  <div>

    <!-- NOT LOGGED IN -->
    <template v-if="!userStore.isLoggedIn">

      <!-- Hero -->
      <div class="bg-white border border-slate-100 rounded-2xl p-8 mb-8 relative overflow-hidden">
        <div class="absolute inset-0 bg-gradient-to-br from-primary-50 to-white pointer-events-none"></div>
        <div class="relative">
          <div class="inline-flex items-center gap-2 bg-primary-50 text-primary-700 text-xs font-medium px-3 py-1 rounded-full mb-4">
            <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
              <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"/>
            </svg>
            1.24M books · ALS + SBERT hybrid engine
          </div>
          <h1 class="text-3xl font-bold text-slate-900 mb-2 tracking-tight">
            Find your next great read.
          </h1>
          <p class="text-slate-500 mb-6 max-w-lg">
            BookRS uses collaborative filtering and semantic embeddings to surface books
            you will love — not just what everyone else is reading.
          </p>
          <div class="flex gap-3">
            <router-link to="/search"
              class="btn-primary flex items-center gap-2 px-5 py-2.5">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0"/>
              </svg>
              Browse Books
            </router-link>
          </div>
        </div>
      </div>

      <!-- Trending -->
      <section class="mb-10">
        <div class="flex items-center justify-between mb-4">
          <div class="flex items-center gap-2">
            <svg class="w-4 h-4 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"/>
            </svg>
            <h2 class="text-base font-semibold text-slate-900">Trending Now</h2>
            <span class="text-xs text-slate-400 font-normal">· updates every 10 min</span>
          </div>
          <router-link to="/trending"
            class="text-xs text-primary-600 hover:text-primary-700 font-medium flex items-center gap-1">
            See all
            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
            </svg>
          </router-link>
        </div>
        <BookGrid :books="store.trending.slice(0, 6)" :is-loading="store.isLoading" />
      </section>

      <!-- Most Popular -->
      <section class="mb-10">
        <div class="flex items-center justify-between mb-4">
          <div class="flex items-center gap-2">
            <svg class="w-4 h-4 text-rose-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7C14 5 16.09 5.777 17.656 7.343A7.975 7.975 0 0120 13a7.975 7.975 0 01-2.343 5.657z"/>
            </svg>
            <h2 class="text-base font-semibold text-slate-900">Most Popular</h2>
          </div>
          <router-link to="/popular"
            class="text-xs text-primary-600 hover:text-primary-700 font-medium flex items-center gap-1">
            See all
            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
            </svg>
          </router-link>
        </div>
        <BookGrid :books="store.popular.slice(0, 6)" :is-loading="store.isLoading" />
      </section>

      <!-- Sign in CTA -->
      <div class="bg-white border border-slate-100 rounded-2xl p-8 text-center mb-8">
        <div class="w-12 h-12 bg-primary-50 rounded-xl flex items-center justify-center mx-auto mb-4">
          <svg class="w-6 h-6 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>
          </svg>
        </div>
        <h3 class="text-lg font-semibold text-slate-900 mb-1">Unlock personalised recommendations</h3>
        <p class="text-sm text-slate-500 mb-5 max-w-sm mx-auto">
          Sign in and rate 5 books to activate the hybrid AI engine combining
          ALS collaborative filtering and SBERT semantic embeddings.
        </p>
        <div class="flex items-center justify-center gap-6 text-xs text-slate-500">
          <div class="flex items-center gap-1.5">
            <div class="w-2 h-2 rounded-full bg-slate-300"></div>
            0 ratings — Popular
          </div>
          <div class="flex items-center gap-1.5">
            <div class="w-2 h-2 rounded-full bg-emerald-400"></div>
            1–4 — Content-based
          </div>
          <div class="flex items-center gap-1.5">
            <div class="w-2 h-2 rounded-full bg-primary-500"></div>
            5+ — Hybrid AI
          </div>
        </div>
      </div>
    </template>

    <!-- LOGGED IN -->
    <template v-else>

      <!-- Status banner -->
      <div class="bg-white border border-slate-100 rounded-2xl p-5 mb-6 flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div class="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0"
            :class="actualMethod === 'hybrid' ? 'bg-primary-50' : actualMethod === 'content' ? 'bg-emerald-50' : 'bg-slate-100'">
            <svg class="w-5 h-5" :class="actualMethod === 'hybrid' ? 'text-primary-600' : actualMethod === 'content' ? 'text-emerald-600' : 'text-slate-500'"
              fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path v-if="actualMethod === 'hybrid'" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>
              <path v-else-if="actualMethod === 'content'" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
              <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7C14 5 16.09 5.777 17.656 7.343A7.975 7.975 0 0120 13a7.975 7.975 0 01-2.343 5.657z"/>
            </svg>
          </div>
          <div>
            <p class="text-sm font-medium text-slate-900">{{ statusTitle }}</p>
            <p class="text-xs text-slate-500">{{ statusDesc }}</p>
          </div>
        </div>
        <!-- Progress for content-based users -->
        <div v-if="actualMethod !== 'popular'" class="hidden sm:flex items-center gap-3">
          <div class="flex gap-1">
            <div v-for="i in 5" :key="i"
              class="w-5 h-1.5 rounded-full transition-colors"
              :class="i <= Math.min(userStore.ratedBooks.size, 5) ? 'bg-primary-500' : 'bg-slate-200'">
            </div>
          </div>
          <span class="text-xs text-slate-400 whitespace-nowrap">{{ Math.min(userStore.ratedBooks.size, 5) }}/5</span>
        </div>
        <router-link v-else to="/search"
          class="text-xs text-primary-600 font-medium hover:text-primary-700 flex-shrink-0">
          Rate books →
        </router-link>
      </div>

      <!-- Recommended For You -->
      <section class="mb-10">
        <div class="flex items-center justify-between mb-4">
          <div class="flex items-center gap-2">
            <svg class="w-4 h-4 text-primary-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"/>
            </svg>
            <h2 class="text-base font-semibold text-slate-900">Recommended for you</h2>
            <span class="badge text-xs"
              :class="{
                'bg-primary-50 text-primary-700': actualMethod === 'hybrid',
                'bg-emerald-50 text-emerald-700': actualMethod === 'content',
                'bg-slate-100 text-slate-600': actualMethod === 'popular',
              }">
              {{ methodLabel }}
            </span>
          </div>
          <button @click="store.fetchRecommendations()"
            class="text-xs text-slate-400 hover:text-slate-600 flex items-center gap-1 transition-colors">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
            </svg>
            Refresh
          </button>
        </div>
        <BookGrid :books="store.recommendations" :is-loading="store.isLoading" />
      </section>

      <!-- Trending -->
      <section class="mb-10">
        <div class="flex items-center justify-between mb-4">
          <div class="flex items-center gap-2">
            <svg class="w-4 h-4 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"/>
            </svg>
            <h2 class="text-base font-semibold text-slate-900">Trending Now</h2>
          </div>
          <router-link to="/trending"
            class="text-xs text-primary-600 hover:text-primary-700 font-medium flex items-center gap-1">
            See all
            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
            </svg>
          </router-link>
        </div>
        <BookGrid :books="store.trending.slice(0, 6)" :is-loading="store.isLoading" />
      </section>

      <!-- Popular -->
      <section class="mb-10">
        <div class="flex items-center justify-between mb-4">
          <div class="flex items-center gap-2">
            <svg class="w-4 h-4 text-rose-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7C14 5 16.09 5.777 17.656 7.343A7.975 7.975 0 0120 13a7.975 7.975 0 01-2.343 5.657z"/>
            </svg>
            <h2 class="text-base font-semibold text-slate-900">Most Popular</h2>
          </div>
          <router-link to="/popular"
            class="text-xs text-primary-600 hover:text-primary-700 font-medium flex items-center gap-1">
            See all
            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
            </svg>
          </router-link>
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
    'hybrid': 'Hybrid AI',
    'content': 'Content-based',
    'popular': 'Popular',
  }
  return map[actualMethod.value]
})

const statusTitle = computed(() => {
  if (actualMethod.value === 'hybrid') return 'Hybrid AI active'
  if (actualMethod.value === 'content') return 'Content-based recommendations'
  return 'Showing popular books'
})

const statusDesc = computed(() => {
  const n = userStore.ratedBooks.size
  if (actualMethod.value === 'hybrid') return 'ALS collaborative filtering + SBERT semantic embeddings'
  if (actualMethod.value === 'content') return `Rate ${5 - n} more book${5-n > 1 ? 's' : ''} to unlock hybrid AI recommendations`
  return 'Rate books to get personalised recommendations'
})

onMounted(async () => {
  await Promise.all([
    store.fetchRecommendations(),
    store.fetchTrending(),
    store.fetchPopular(),
  ])
})
</script>

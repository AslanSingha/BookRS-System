<template>
  <div>

    <!-- NOT LOGGED IN -->
    <template v-if="!userStore.isLoggedIn">
      <!-- Hero -->
      <div class="bg-white border border-slate-100 rounded-2xl p-8 mb-8 relative overflow-hidden">
        <div class="absolute inset-0 bg-gradient-to-br from-primary-50 to-white pointer-events-none"></div>
        <div class="relative">
          <div class="flex flex-wrap items-center gap-2 mb-5">
            <div class="inline-flex items-center gap-1.5 bg-primary-50 text-primary-700 text-xs font-semibold px-3 py-1.5 rounded-full">883,468 Unique Books</div>
            <div class="inline-flex items-center gap-1.5 bg-blue-50 text-blue-700 text-xs font-semibold px-3 py-1.5 rounded-full">ALS Collaborative Filtering</div>
            <div class="inline-flex items-center gap-1.5 bg-violet-50 text-violet-700 text-xs font-semibold px-3 py-1.5 rounded-full">SBERT Semantic Embeddings</div>
            <div class="inline-flex items-center gap-1.5 bg-emerald-50 text-emerald-700 text-xs font-semibold px-3 py-1.5 rounded-full">11 Genres · 666K Users</div>
          </div>
          <h1 class="text-3xl font-bold text-slate-900 mb-2 tracking-tight">Discover your next great read.</h1>
          <p class="text-slate-500 mb-6 max-w-lg">BookRS searches 883,468 unique books using ALS collaborative filtering and SBERT semantic embeddings — personalised to your taste.</p>
          <div class="flex gap-3">
            <router-link to="/search" class="btn-primary flex items-center gap-2 px-5 py-2.5">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0"/></svg>
              Search Books
            </router-link>
          </div>
        </div>
      </div>

      <!-- Guest: Trending -->
      <section class="mb-10">
        <div class="flex items-center justify-between mb-4">
          <div>
            <h2 class="text-xl font-bold text-slate-900">Trending This Week</h2>
            <p class="text-sm text-slate-500 mt-0.5">Most popular books right now</p>
          </div>
          <router-link to="/trending" class="text-sm text-primary-600 hover:text-primary-700 font-medium">See all →</router-link>
        </div>
        <BookGrid :books="store.trending.slice(0, 10)" :is-loading="store.isLoading" :onCardClick="handleRecClick" />
      </section>

      <!-- Guest: Popular -->
      <section class="mb-10">
        <div class="flex items-center justify-between mb-4">
          <div>
            <h2 class="text-xl font-bold text-slate-900">Most Popular</h2>
            <p class="text-sm text-slate-500 mt-0.5">Highest rated across all genres</p>
          </div>
          <router-link to="/popular" class="text-sm text-primary-600 hover:text-primary-700 font-medium">See all →</router-link>
        </div>
        <BookGrid :books="store.popular.slice(0, 10)" :is-loading="store.isLoading" :onCardClick="handleRecClick" />
      </section>
    </template>

    <!-- LOGGED IN -->
    <template v-else>

      <!-- Welcome bar -->
      <div class="flex items-center justify-between mb-6">
        <div>
          <h1 class="text-2xl font-bold text-slate-900">Welcome back, {{ userStore.userId }}</h1>
          <p class="text-sm text-slate-500 mt-0.5">Your personalised reading feed</p>
        </div>
        <div class="flex items-center gap-2">
          <span class="inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-full"
            :class="actualMethod === 'hybrid' ? 'bg-primary-50 text-primary-700' : actualMethod === 'content' ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-600'">
            {{ methodLabel }}
          </span>
        </div>
      </div>

      <!-- SECTION 1: Because you searched X -->
      <section v-if="store.becauseSearched.length > 0" class="mb-10">
        <div class="flex items-center justify-between mb-4">
          <div>
            <div class="flex items-center gap-2 mb-1">
              <span class="text-xs font-semibold bg-violet-100 text-violet-700 px-2 py-0.5 rounded-full">Search Influence</span>
            </div>
            <h2 class="text-xl font-bold text-slate-900">Because you searched "<span class="text-primary-600">{{ store.lastSearchQuery }}</span>"</h2>
            <p class="text-sm text-slate-500 mt-0.5">Books matching your recent search interest</p>
          </div>
        </div>
        <BookGrid :books="store.becauseSearched" :is-loading="sectionsLoading" :onCardClick="handleRecClick" />
      </section>

      <!-- SECTION 2: Because you rated [book] -->
      <section v-if="store.becauseRated.length > 0" class="mb-10">
        <div class="flex items-center justify-between mb-4">
          <div>
            <div class="flex items-center gap-2 mb-1">
              <span class="text-xs font-semibold bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded-full">Content Based</span>
            </div>
            <h2 class="text-xl font-bold text-slate-900">
              Because you rated
              <span class="text-primary-600">
                "{{ store.lastRatedBook?.title?.slice(0,40) || 'a book you loved' }}"
              </span>
            </h2>
            <p class="text-sm text-slate-500 mt-0.5">Books with similar themes and style</p>
          </div>
        </div>
        <BookGrid :books="store.becauseRated" :is-loading="sectionsLoading" :onCardClick="handleRecClick" />
      </section>

      <!-- SECTION 3: Main hybrid recommendations -->
      <section class="mb-10">
        <div class="flex items-center justify-between mb-4">
          <div>
            <div class="flex items-center gap-2 mb-1">
              <span class="text-xs font-semibold bg-primary-100 text-primary-700 px-2 py-0.5 rounded-full">Hybrid AI</span>
            </div>
            <h2 class="text-xl font-bold text-slate-900">Top Picks For You</h2>
            <p class="text-sm text-slate-500 mt-0.5">SBERT + ALS collaborative filtering combined</p>
          </div>
        </div>
        <BookGrid :books="store.recommendations" :is-loading="store.isLoading" :onCardClick="handleRecClick" />
      </section>

      <!-- SECTION 4: Readers like you enjoyed -->
      <section v-if="store.collaborativePicks.length > 0" class="mb-10">
        <div class="flex items-center justify-between mb-4">
          <div>
            <div class="flex items-center gap-2 mb-1">
              <span class="text-xs font-semibold bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full">Collaborative</span>
            </div>
            <h2 class="text-xl font-bold text-slate-900">Readers Like You Also Enjoyed</h2>
            <p class="text-sm text-slate-500 mt-0.5">Based on users with similar reading taste</p>
          </div>
        </div>
        <BookGrid :books="store.collaborativePicks" :is-loading="sectionsLoading" :onCardClick="handleRecClick" />
      </section>

      <!-- SECTION 5: Popular in favourite genre -->
      <section v-if="store.genrePopular.length > 0" class="mb-10">
        <div class="flex items-center justify-between mb-4">
          <div>
            <div class="flex items-center gap-2 mb-1">
              <span class="text-xs font-semibold bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full">Genre Pick</span>
            </div>
            <h2 class="text-xl font-bold text-slate-900">
              Popular in
              <span class="text-primary-600 capitalize">{{ store.topGenre }}</span>
            </h2>
            <p class="text-sm text-slate-500 mt-0.5">Top rated books in your favourite genre</p>
          </div>
        </div>
        <BookGrid :books="store.genrePopular" :is-loading="sectionsLoading" :onCardClick="handleRecClick" />
      </section>

      <!-- SECTION 6: Trending -->
      <section class="mb-10">
        <div class="flex items-center justify-between mb-4">
          <div>
            <div class="flex items-center gap-2 mb-1">
              <span class="text-xs font-semibold bg-rose-100 text-rose-700 px-2 py-0.5 rounded-full">Trending</span>
            </div>
            <h2 class="text-xl font-bold text-slate-900">Trending This Week</h2>
            <p class="text-sm text-slate-500 mt-0.5">Most popular books across all readers</p>
          </div>
          <router-link to="/trending" class="text-sm text-primary-600 hover:text-primary-700 font-medium">See all →</router-link>
        </div>
        <BookGrid :books="store.trending.slice(0, 10)" :is-loading="store.isLoading" :onCardClick="handleRecClick" />
      </section>

    </template>

  </div>
</template>

<script setup>
import { onMounted, computed, ref } from 'vue'
import { useBookStore } from '../stores/books'
import { useUserStore } from '../stores/user'
import BookGrid from '../components/BookGrid.vue'

const store = useBookStore()
const userStore = useUserStore()
const sectionsLoading = ref(false)

const actualMethod = computed(() => {
  if (!userStore.isLoggedIn) return 'popular'
  if (userStore.ratedBooks.size === 0) return 'popular'
  if (userStore.ratedBooks.size < 5) return 'content'
  return 'hybrid'
})

const methodLabel = computed(() => {
  if (actualMethod.value === 'hybrid') return 'Hybrid AI Active'
  if (actualMethod.value === 'content') return 'Content-Based'
  return 'Popularity-Based'
})

async function handleRecClick(bookId) {
  await userStore.logSearchClick(bookId)
}

onMounted(async () => {
  await Promise.all([
    store.fetchRecommendations(),
    store.fetchTrending(10),
    store.fetchPopular(10),
  ])
  if (userStore.isLoggedIn) {
    sectionsLoading.value = true
    try {
      await store.fetchPersonalisedSections()
    } finally {
      sectionsLoading.value = false
    }
  }
})
</script>

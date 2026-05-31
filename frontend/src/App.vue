<template>
  <div class="min-h-screen bg-slate-50">

    <!-- Navbar -->
    <header class="bg-white border-b border-slate-100 sticky top-0 z-50">
      <div class="max-w-7xl mx-auto px-4 sm:px-6">
        <div class="flex items-center justify-between h-14">

          <!-- Logo -->
          <router-link to="/" class="flex items-center gap-2.5 flex-shrink-0">
            <div class="w-7 h-7 bg-primary-600 rounded-lg flex items-center justify-center">
              <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
              </svg>
            </div>
            <span class="font-semibold text-slate-900 text-base tracking-tight">BookRS</span>
          </router-link>

          <!-- Search -->
          <div class="flex-1 max-w-lg mx-6 hidden sm:block">
            <form @submit.prevent="handleSearch" class="relative">
              <div class="absolute inset-y-0 left-3 flex items-center pointer-events-none">
                <svg class="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0"/>
                </svg>
              </div>
              <input
                v-model="searchQuery"
                type="text"
                placeholder="Search books, authors, topics..."
                class="w-full pl-9 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-400 transition-all"
              />
            </form>
          </div>

          <!-- Nav -->
          <nav class="flex items-center gap-1">
            <router-link to="/" class="btn-ghost hidden md:flex items-center gap-1.5">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/>
              </svg>
              Home
            </router-link>
            <router-link to="/trending" class="btn-ghost hidden md:flex items-center gap-1.5">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"/>
              </svg>
              Trending
            </router-link>
            <router-link to="/popular" class="btn-ghost hidden md:flex items-center gap-1.5">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7C14 5 16.09 5.777 17.656 7.343A7.975 7.975 0 0120 13a7.975 7.975 0 01-2.343 5.657z"/>
              </svg>
              Popular
            </router-link>

            <!-- Divider -->
            <div class="w-px h-5 bg-slate-200 mx-1 hidden md:block"></div>

            <!-- User -->
            <div v-if="userStore.isLoggedIn" class="flex items-center gap-1">
              <router-link to="/profile"
                class="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-slate-100 transition-colors">
                <div class="w-6 h-6 rounded-full bg-primary-100 flex items-center justify-center">
                  <span class="text-xs font-semibold text-primary-700">{{ userStore.userId.charAt(0).toUpperCase() }}</span>
                </div>
                <span class="text-sm font-medium text-slate-700 hidden md:block">{{ userStore.userId }}</span>
                <span v-if="userStore.ratedBooks.size > 0"
                  class="text-xs bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded-md font-medium hidden md:block">
                  {{ userStore.ratedBooks.size }} rated
                </span>
              </router-link>
              <button @click="userStore.logout()"
                class="p-1.5 rounded-lg hover:bg-slate-100 transition-colors text-slate-400 hover:text-slate-600">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/>
                </svg>
              </button>
            </div>
            <button v-else @click="showLogin = true"
              class="btn-primary ml-1">
              Sign in
            </button>
          </nav>
        </div>
      </div>
    </header>

    <!-- Login Modal -->
    <Transition name="fade">
      <div v-if="showLogin"
        class="fixed inset-0 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center z-50 p-4"
        @click.self="showLogin = false">
        <div class="bg-white rounded-2xl p-6 w-full max-w-sm shadow-xl">
          <div class="flex items-center justify-between mb-5">
            <div>
              <h2 class="text-lg font-semibold text-slate-900">Sign in to BookRS</h2>
              <p class="text-sm text-slate-500 mt-0.5">Enter any username to get started</p>
            </div>
            <button @click="showLogin = false"
              class="p-1.5 rounded-lg hover:bg-slate-100 text-slate-400">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
              </svg>
            </button>
          </div>
          <input
            v-model="loginId"
            type="text"
            placeholder="Username (e.g. 111, john, rin)"
            class="w-full px-3.5 py-2.5 border border-slate-200 rounded-lg text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-400 mb-3"
            @keyup.enter="handleLogin"
            autofocus
          />
          <div class="flex gap-2">
            <button @click="handleLogin"
              class="flex-1 bg-primary-600 text-white py-2.5 rounded-lg text-sm font-medium hover:bg-primary-700 transition-colors">
              Sign in
            </button>
            <button @click="showLogin = false"
              class="flex-1 bg-slate-100 text-slate-600 py-2.5 rounded-lg text-sm font-medium hover:bg-slate-200 transition-colors">
              Cancel
            </button>
          </div>
          <p class="text-xs text-slate-400 text-center mt-3">
            Use ID 111 or 123 for full hybrid recommendations
          </p>
        </div>
      </div>
    </Transition>

    <!-- Main -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 py-6">
      <router-view />
    </main>

    <!-- Footer -->
    <footer class="border-t border-slate-100 mt-16 py-8">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 flex flex-col sm:flex-row items-center justify-between gap-3">
        <div class="flex items-center gap-2">
          <div class="w-5 h-5 bg-primary-600 rounded-md flex items-center justify-center">
            <svg class="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
            </svg>
          </div>
          <span class="text-sm font-medium text-slate-600">BookRS</span>
        </div>
        <p class="text-xs text-slate-400">
          AI-Powered Book Recommendation System · Institute of Technology of Cambodia 2026
        </p>
        <div class="flex items-center gap-4 text-xs text-slate-400">
          <a href="https://github.com/AslanSingha/bookrss" target="_blank"
            class="hover:text-slate-600 transition-colors flex items-center gap-1">
            <svg class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
            </svg>
            GitHub
          </a>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from './stores/user'

const router = useRouter()
const userStore = useUserStore()
const searchQuery = ref('')
const showLogin = ref(false)
const loginId = ref('')

function handleSearch() {
  if (searchQuery.value.trim()) {
    router.push({ name: 'Search', query: { q: searchQuery.value } })
    searchQuery.value = ''
  }
}

function handleLogin() {
  if (loginId.value.trim()) {
    userStore.login(loginId.value.trim())
    showLogin.value = false
    loginId.value = ''
  }
}
</script>

<style>
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>

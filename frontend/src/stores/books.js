import { defineStore } from 'pinia'
import { ref } from 'vue'
import { recommendApi, searchApi } from '../services/api'
import { useUserStore } from './user'

export const useBookStore = defineStore('books', () => {
  const recommendations = ref([])
  const popular = ref([])
  const trending = ref([])
  const searchResults = ref([])
  const isLoading = ref(false)
  const recommendMethod = ref('popular')

  async function fetchRecommendations() {
    isLoading.value = true
    try {
      const userStore = useUserStore()

      // Not logged in → show trending (different from popular section)
      if (!userStore.isLoggedIn) {
        const res = await recommendApi.getTrending(10)
        recommendations.value = res.data.recommendations
        recommendMethod.value = 'popular'
        return
      }

      const userId       = userStore.userId
      const ratedBooks   = [...userStore.ratedBooks.keys()].join(',')
      const favBooks     = [...userStore.favorites].join(',')
      const clickedBooks = [...userStore.searchClicks].join(',')
      const viewedBooks  = [...userStore.recentViews].join(',')
      const res = await recommendApi.getHybrid(
        userId, 10, ratedBooks, favBooks, clickedBooks, viewedBooks
      )
      recommendations.value = res.data.recommendations
      recommendMethod.value = res.data.method
    } catch (e) {
      console.error('Failed to fetch recommendations:', e)
    } finally {
      isLoading.value = false
    }
  }

  async function fetchPopular(genre = null) {
    isLoading.value = true
    try {
      const res = await recommendApi.getPopular(30, genre)
      popular.value = res.data.recommendations
    } catch (e) {
      console.error('Failed to fetch popular:', e)
    } finally {
      isLoading.value = false
    }
  }

  async function fetchTrending(n = 30) {
    isLoading.value = true
    try {
      const res = await recommendApi.getTrending(n)
      trending.value = res.data.recommendations
    } catch (e) {
      console.error('Failed to fetch trending:', e)
    } finally {
      isLoading.value = false
    }
  }

  async function search(query) {
    if (!query.trim()) return
    isLoading.value = true
    try {
      const res = await searchApi.search(query, 30)
      searchResults.value = res.data.results
    } catch (e) {
      console.error('Search failed:', e)
    } finally {
      isLoading.value = false
    }
  }

  return {
    recommendations, popular, trending, searchResults,
    isLoading, recommendMethod,
    fetchRecommendations, fetchPopular, fetchTrending, search
  }
})

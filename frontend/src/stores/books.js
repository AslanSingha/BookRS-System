import { defineStore } from 'pinia'
import { ref } from 'vue'
import { recommendApi, searchApi } from '../services/api'

export const useBookStore = defineStore('books', () => {
  const recommendations = ref([])
  const popular = ref([])
  const trending = ref([])
  const searchResults = ref([])
  const isLoading = ref(false)
  const currentUserId = ref('user_1')  // default user for demo

  async function fetchRecommendations() {
    isLoading.value = true
    try {
      const res = await recommendApi.getHybrid(currentUserId.value)
      recommendations.value = res.data.recommendations
    } catch (e) {
      console.error('Failed to fetch recommendations:', e)
    } finally {
      isLoading.value = false
    }
  }

  async function fetchPopular(genre = null) {
    isLoading.value = true
    try {
      const res = await recommendApi.getPopular(20, genre)
      popular.value = res.data.recommendations
    } catch (e) {
      console.error('Failed to fetch popular:', e)
    } finally {
      isLoading.value = false
    }
  }

  async function fetchTrending() {
    isLoading.value = true
    try {
      const res = await recommendApi.getTrending(20)
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
      const res = await searchApi.search(query, 20)
      searchResults.value = res.data.results
    } catch (e) {
      console.error('Search failed:', e)
    } finally {
      isLoading.value = false
    }
  }

  return {
    recommendations, popular, trending, searchResults,
    isLoading, currentUserId,
    fetchRecommendations, fetchPopular, fetchTrending, search
  }
})

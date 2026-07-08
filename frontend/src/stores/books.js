import { defineStore } from 'pinia'
import { ref } from 'vue'
import { recommendApi } from '../services/api'
import { useUserStore } from './user'

export const useBookStore = defineStore('books', () => {
  // existing
  const recommendations   = ref([])
  const popular           = ref([])
  const trending          = ref([])
  const searchResults     = ref([])
  const isLoading         = ref(false)
  const recommendMethod   = ref('popular')

  // NEW — Netflix-style sections
  const becauseSearched   = ref([])   // "Because you searched X"
  const becauseRated      = ref([])   // "Because you rated [book]"
  const collaborativePicks= ref([])   // "Readers like you enjoyed"
  const genrePopular      = ref([])   // "Popular in [genre]"
  const lastSearchQuery   = ref('')   // label for section 1
  const lastRatedBook     = ref(null) // label for section 2
  const topGenre          = ref('')   // label for section 4

  async function fetchRecommendations() {
    isLoading.value = true
    try {
      const userStore = useUserStore()
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

  // NEW — fetch all Netflix-style sections
  async function fetchPersonalisedSections() {
    const userStore = useUserStore()
    if (!userStore.isLoggedIn) return

    const userId     = userStore.userId
    const ratedBooks = [...userStore.ratedBooks.keys()]
    const favBooks   = [...userStore.favorites].join(',')
    const clickedBooks = [...userStore.searchClicks].join(',')
    const viewedBooks  = [...userStore.recentViews].join(',')

    // Section 1: Because you searched X
    const query = userStore.lastQuery
    if (query) {
      lastSearchQuery.value = query
      try {
        const res = await recommendApi.getBecauseSearched(query, 10)
        becauseSearched.value = res.data.recommendations
      } catch (e) { becauseSearched.value = [] }
    }

    // Section 2: Because you rated [book]
    // Find most recently rated book with rating >= 4
    if (ratedBooks.length > 0) {
      // Get the last rated book (most recent key in ratedBooks map)
      const ratedEntries = [...userStore.ratedBooks.entries()]
      const highRated = ratedEntries.filter(([, r]) => r >= 4)
      if (highRated.length > 0) {
        const [topBookId, ] = highRated[highRated.length - 1]
        try {
          const bookRes = await fetch(
            `http://localhost:8000/api/v1/books/${topBookId}`
          )
          const bookData = await bookRes.json()
          lastRatedBook.value = bookData
          const res = await recommendApi.getBecauseRated(topBookId, 10)
          becauseRated.value = res.data.recommendations
        } catch (e) { becauseRated.value = [] }
      }
    }

    // Section 3: Collaborative picks — use similar books to top rated
    // to make it different from Top Picks
    try {
      const ratedEntries = [...userStore.ratedBooks.entries()]
      const topRated = ratedEntries.sort((a,b) => b[1]-a[1])[0]
      if (topRated) {
        const res = await recommendApi.getBecauseRated(topRated[0], 10)
        // Filter out books already in recommendations
        const recIds = new Set(recommendations.value.map(b => b.book_id))
        collaborativePicks.value = (res.data.recommendations || [])
          .filter(b => !recIds.has(b.book_id))
      } else {
        collaborativePicks.value = []
      }
    } catch (e) { collaborativePicks.value = [] }

    // Section 4: Popular in favourite genre
    // Compute top genre from rated books
    const genreCount = {}
    recommendations.value.forEach(b => {
      if (b.genre) genreCount[b.genre] = (genreCount[b.genre] || 0) + 1
    })
    const genre = Object.entries(genreCount).sort((a,b)=>b[1]-a[1])[0]?.[0]
    if (genre) {
      topGenre.value = genre
      try {
        const res = await recommendApi.getByGenre(genre, 10)
        genrePopular.value = res.data.recommendations
      } catch (e) { genrePopular.value = [] }
    }
  }

  async function fetchPopular(n = 10, genre = null) {
    try {
      const res = await recommendApi.getPopular(n, genre)
      popular.value = res.data.recommendations || []
    } catch (e) {
      console.error('Failed to fetch popular:', e)
      popular.value = []
    }
  }

  async function fetchTrending(n = 10) {
    try {
      const res = await recommendApi.getTrending(n)
      trending.value = res.data.recommendations || []
    } catch (e) {
      console.error('Failed to fetch trending:', e)
      trending.value = []
    }
  }

  return {
    recommendations, popular, trending, searchResults,
    isLoading, recommendMethod,
    // NEW sections
    becauseSearched, becauseRated, collaborativePicks, genrePopular,
    lastSearchQuery, lastRatedBook, topGenre,
    // functions
    fetchRecommendations, fetchPopular, fetchTrending,
    fetchPersonalisedSections,
  }
})

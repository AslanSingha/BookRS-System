import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../services/api'

export const useUserStore = defineStore('user', () => {
  const userId = ref(localStorage.getItem('bookrs_user_id') || '')
  const favorites = ref(new Set(JSON.parse(localStorage.getItem('bookrs_favorites') || '[]')))
  const ratedBooks = ref(new Map(JSON.parse(localStorage.getItem('bookrs_ratings') || '[]')))
  const searchClicks = ref(new Set(JSON.parse(localStorage.getItem('bookrs_clicks') || '[]')))
  const lastQuery = ref(localStorage.getItem('bookrs_last_query') || '')
  const recentViews = ref(new Set(JSON.parse(localStorage.getItem('bookrs_views') || '[]')))
  const isLoggedIn = ref(!!userId.value)

  async function login(id) {
    userId.value = id
    isLoggedIn.value = true
    localStorage.setItem('bookrs_user_id', id)
    // Sync UCSD ratings if user exists in dataset
    try {
      await api.post('/users/login', { user_id: id })
    } catch (e) {
      console.error('Login sync failed:', e)
    }
    // Load history from DB (includes synced UCSD ratings)
    await loadHistoryFromDB(id)
  }

  async function loadHistoryFromDB(id) {
    try {
      // Load combined ratings (UCSD + app) 
      const [ratingsRes, actionsRes] = await Promise.all([
        api.get(`/users/${id}/all-ratings`),
        api.get(`/actions/${id}`)
      ])

      const newRatings = new Map()
      const newFavorites = new Set()

      // Load all ratings (UCSD + app combined)
      for (const r of ratingsRes.data) {
        newRatings.set(r.book_id, r.rating)
      }

      // Load favorites and other actions
      for (const action of actionsRes.data) {
        if (action.action_type === 'favorite') {
          newFavorites.add(action.book_id)
        }
      }

      const newClicks = new Set()
      const newViews  = new Set()

      for (const action of actionsRes.data) {
        if (action.action_type === 'search_click') newClicks.add(action.book_id)
        if (action.action_type === 'view')         newViews.add(action.book_id)
      }

      ratedBooks.value   = newRatings
      favorites.value    = newFavorites
      searchClicks.value = newClicks
      recentViews.value  = newViews

      // Sync to localStorage
      localStorage.setItem('bookrs_ratings',  JSON.stringify([...newRatings.entries()]))
      localStorage.setItem('bookrs_favorites', JSON.stringify([...newFavorites]))
      localStorage.setItem('bookrs_clicks',    JSON.stringify([...newClicks]))
      localStorage.setItem('bookrs_views',     JSON.stringify([...newViews]))

      console.log(`Loaded ${newRatings.size} ratings, ${newFavorites.size} favorites, ${newClicks.size} clicks, ${newViews.size} views from DB`)
    } catch (e) {
      console.error('Failed to load history from DB:', e)
    }
  }

  function setLastQuery(q) {
    lastQuery.value = q
    localStorage.setItem('bookrs_last_query', q)
  }

  function logout() {
    userId.value = ''
    isLoggedIn.value = false
    favorites.value = new Set()
    ratedBooks.value = new Map()
    searchClicks.value = new Set()
    recentViews.value  = new Set()
    localStorage.removeItem('bookrs_user_id')
    localStorage.removeItem('bookrs_favorites')
    localStorage.removeItem('bookrs_ratings')
    localStorage.removeItem('bookrs_clicks')
    localStorage.removeItem('bookrs_last_query')
    lastQuery.value = ''
    localStorage.removeItem('bookrs_views')
  }

  async function logAction(bookId, actionType, value = 0) {
    if (!userId.value) return
    try {
      await api.post('/actions/', {
        user_id: userId.value,
        book_id: bookId,
        action_type: actionType,
        value: value
      })
    } catch (e) {
      console.error('Failed to log action:', e)
    }
  }

  async function toggleFavorite(bookId) {
    if (!isLoggedIn.value) return
    try {
      const res = await fetch('http://localhost:8000/api/v1/actions/toggle-favorite', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId.value, book_id: bookId, action_type: 'favorite', value: 1 })
      })
      const data = await res.json()
      if (data.favorited) {
        favorites.value.add(bookId)
      } else {
        favorites.value.delete(bookId)
      }
      localStorage.setItem('bookrs_favorites', JSON.stringify([...favorites.value]))
    } catch (e) {
      // Fallback: toggle locally
      if (favorites.value.has(bookId)) {
        favorites.value.delete(bookId)
      } else {
        favorites.value.add(bookId)
      }
      localStorage.setItem('bookrs_favorites', JSON.stringify([...favorites.value]))
    }
  }

  async function rateBook(bookId, rating) {
    if (!isLoggedIn.value) return
    ratedBooks.value.set(bookId, rating)
    localStorage.setItem('bookrs_ratings', JSON.stringify([...ratedBooks.value.entries()]))
    // Save to interactions table (used by ALS + SBERT)
    try {
      await fetch(`http://localhost:8000/api/v1/users/${userId.value}/ratings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ book_id: bookId, rating: rating, is_reviewed: 0 })
      })
    } catch (e) { console.error('Failed to save rating to DB:', e) }
    // Also log to user_actions (activity tab)
    await logAction(bookId, 'rating', rating)
  }

  async function deleteRating(bookId) {
    if (!isLoggedIn.value) return
    try {
      await fetch(`http://localhost:8000/api/v1/users/${userId.value}/ratings/${bookId}`, {
        method: 'DELETE'
      })
    } catch (e) { /* continue */ }
    ratedBooks.value.delete(bookId)
    localStorage.setItem('bookrs_ratings', JSON.stringify([...ratedBooks.value.entries()]))
  }

  async function logView(bookId) {
    if (!isLoggedIn.value) return
    recentViews.value.add(bookId)
    localStorage.setItem('bookrs_views', JSON.stringify([...recentViews.value]))
    await logAction(bookId, 'view', 1)
  }

  async function logSearchClick(bookId) {
    if (!isLoggedIn.value) return
    searchClicks.value.add(bookId)
    localStorage.setItem('bookrs_clicks', JSON.stringify([...searchClicks.value]))
    await logAction(bookId, 'search_click', 1)
  }

  // Auto-load history if already logged in
  async function initializeSession() {
    if (userId.value) {
      await loadHistoryFromDB(userId.value)
    }
  }

  return {
    userId, isLoggedIn, favorites, ratedBooks,
    login, logout, logAction, toggleFavorite, rateBook, deleteRating,
    logView, logSearchClick, searchClicks, recentViews, lastQuery, setLastQuery,
    loadHistoryFromDB, initializeSession
  }
})

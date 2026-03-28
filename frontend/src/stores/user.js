import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../services/api'

export const useUserStore = defineStore('user', () => {
  const userId = ref(localStorage.getItem('bookrs_user_id') || '')
  const favorites = ref(new Set(JSON.parse(localStorage.getItem('bookrs_favorites') || '[]')))
  const ratedBooks = ref(new Map(JSON.parse(localStorage.getItem('bookrs_ratings') || '[]')))
  const isLoggedIn = ref(!!userId.value)

  async function login(id) {
    userId.value = id
    isLoggedIn.value = true
    localStorage.setItem('bookrs_user_id', id)
    // Load history from DB
    await loadHistoryFromDB(id)
  }

  async function loadHistoryFromDB(id) {
    try {
      const res = await api.get(`/actions/${id}`)
      const actions = res.data

      // Rebuild ratings and favorites from DB
      const newRatings = new Map()
      const newFavorites = new Set()

      for (const action of actions) {
        if (action.action_type === 'rating') {
          // Keep the latest rating for each book
          if (!newRatings.has(action.book_id) ||
              new Date(action.created_at) > new Date(newRatings.get(action.book_id).created_at)) {
            newRatings.set(action.book_id, action.value)
          }
        } else if (action.action_type === 'favorite') {
          newFavorites.add(action.book_id)
        }
      }

      ratedBooks.value = newRatings
      favorites.value = newFavorites

      // Sync to localStorage
      localStorage.setItem('bookrs_ratings', JSON.stringify([...newRatings.entries()]))
      localStorage.setItem('bookrs_favorites', JSON.stringify([...newFavorites]))

      console.log(`Loaded ${newRatings.size} ratings, ${newFavorites.size} favorites from DB`)
    } catch (e) {
      console.error('Failed to load history from DB:', e)
    }
  }

  function logout() {
    userId.value = ''
    isLoggedIn.value = false
    favorites.value = new Set()
    ratedBooks.value = new Map()
    localStorage.removeItem('bookrs_user_id')
    localStorage.removeItem('bookrs_favorites')
    localStorage.removeItem('bookrs_ratings')
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
    if (favorites.value.has(bookId)) {
      favorites.value.delete(bookId)
    } else {
      favorites.value.add(bookId)
      await logAction(bookId, 'favorite', 1)
    }
    localStorage.setItem('bookrs_favorites', JSON.stringify([...favorites.value]))
  }

  async function rateBook(bookId, rating) {
    ratedBooks.value.set(bookId, rating)
    localStorage.setItem('bookrs_ratings', JSON.stringify([...ratedBooks.value.entries()]))
    await logAction(bookId, 'rating', rating)
  }

  async function logView(bookId) {
    await logAction(bookId, 'view', 1)
  }

  // Auto-load history if already logged in
  async function initializeSession() {
    if (userId.value) {
      await loadHistoryFromDB(userId.value)
    }
  }

  return {
    userId, isLoggedIn, favorites, ratedBooks,
    login, logout, logAction, toggleFavorite, rateBook, logView,
    loadHistoryFromDB, initializeSession
  }
})

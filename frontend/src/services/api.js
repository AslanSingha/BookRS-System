import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  timeout: 30000,
})

export const booksApi = {
  getBooks: (page = 1, genre = null) =>
    api.get('/books/', { params: { page, genre } }),
  getBook: (bookId) =>
    api.get(`/books/${bookId}`),
  getGenres: () =>
    api.get('/books/genres'),
}

export const recommendApi = {
  getHybrid: (userId, n = 10, ratedBooks = '', favBooks = '', clickedBooks = '', viewedBooks = '') =>
    api.get(`/recommendations/hybrid/${userId}`, {
      params: {
        n,
        rated_books:   ratedBooks   || undefined,
        fav_books:     favBooks     || undefined,
        clicked_books: clickedBooks || undefined,
        viewed_books:  viewedBooks  || undefined,
      }
    }),
  getSimilar: (bookId, n = 10) =>
    api.get(`/recommendations/similar/${bookId}`, { params: { n } }),
  getPopular: (n = 10, genre = null) =>
    api.get('/recommendations/popular', { params: { n, genre } }),
  getTrending: (n = 10) =>
    api.get('/recommendations/trending', { params: { n } }),
}

export const searchApi = {
  search: (query, n = 10) =>
    api.get('/search/', { params: { q: query, n } }),
  personalized: (query, userId, n = 10, ratedBooks = '') =>
    api.get('/search/personalized', {
      params: { q: query, user_id: userId, n, rated_books: ratedBooks || undefined }
    }),
}

export const actionsApi = {
  logAction: (data) => api.post('/actions/', data),
  getUserActions: (userId) => api.get(`/actions/${userId}`),
  getUserFavorites: (userId) => api.get(`/actions/${userId}/favorites`),
}

export default api

export const usersApi = {
  login: (userId) => api.post('/users/login', { user_id: userId }),
}

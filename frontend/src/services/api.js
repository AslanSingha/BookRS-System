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
  getHybrid: (userId, n = 10) =>
    api.get(`/recommendations/hybrid/${userId}`, { params: { n } }),
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
}

export default api

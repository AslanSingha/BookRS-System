import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'Home', component: () => import('../views/HomeView.vue') },
  { path: '/search', name: 'Search', component: () => import('../views/SearchView.vue') },
  { path: '/book/:id', name: 'BookDetail', component: () => import('../views/BookDetailView.vue') },
  { path: '/trending', name: 'Trending', component: () => import('../views/TrendingView.vue') },
  { path: '/popular', name: 'Popular', component: () => import('../views/PopularView.vue') },
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router

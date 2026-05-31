<template>
  <div>
    <!-- Loading skeleton -->
    <div v-if="isLoading"
      class="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 gap-3 md:gap-4">
      <div v-for="i in 6" :key="i" class="animate-pulse">
        <div class="bg-slate-100 rounded-xl" style="aspect-ratio:2/3"></div>
        <div class="mt-2 space-y-1.5 p-1">
          <div class="h-3 bg-slate-100 rounded w-4/5"></div>
          <div class="h-3 bg-slate-100 rounded w-3/5"></div>
          <div class="h-2.5 bg-slate-100 rounded w-2/5"></div>
        </div>
      </div>
    </div>

    <!-- Empty state -->
    <div v-else-if="books.length === 0"
      class="flex flex-col items-center justify-center py-16 text-center">
      <div class="w-12 h-12 rounded-xl bg-slate-100 flex items-center justify-center mb-3">
        <svg class="w-6 h-6 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
        </svg>
      </div>
      <p class="text-sm font-medium text-slate-600">No books found</p>
      <p class="text-xs text-slate-400 mt-1">Try a different search or category</p>
    </div>

    <!-- Books grid -->
    <div v-else
      class="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 gap-3 md:gap-4">
      <BookCard v-for="book in books" :key="book.book_id" :book="book" />
    </div>
  </div>
</template>

<script setup>
import BookCard from './BookCard.vue'

defineProps({
  books: { type: Array, default: () => [] },
  isLoading: { type: Boolean, default: false }
})
</script>

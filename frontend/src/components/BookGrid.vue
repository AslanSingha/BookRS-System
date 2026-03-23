<template>
  <div>
    <div v-if="isLoading" class="flex justify-center py-12">
      <div class="animate-spin text-4xl">📚</div>
    </div>
    <div v-else-if="books.length === 0" class="text-center py-12 text-gray-400">
      <p class="text-4xl mb-3">📭</p>
      <p>No books found</p>
    </div>
    <div v-else class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
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

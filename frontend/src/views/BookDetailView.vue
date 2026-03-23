<template>
  <div v-if="book" class="max-w-4xl mx-auto">
    <div class="card mb-6">
      <div class="flex gap-6">
        <!-- Cover -->
        <div class="w-40 h-56 bg-gradient-to-br from-primary-100 to-primary-200 rounded-lg flex-shrink-0 flex items-center justify-center overflow-hidden">
          <img v-if="book.image_url && !imgError"
               :src="book.image_url" :alt="book.title"
               class="w-full h-full object-cover"
               @error="imgError = true" />
          <span v-else class="text-6xl">📖</span>
        </div>

        <!-- Info -->
        <div class="flex-1">
          <span v-if="book.genre" class="text-xs bg-primary-50 text-primary-700 px-3 py-1 rounded-full font-medium">
            {{ book.genre }}
          </span>
          <h1 class="text-2xl font-bold mt-2 mb-1">{{ book.title }}</h1>
          <p class="text-gray-500 mb-3">by {{ book.authors }}</p>

          <div class="flex items-center gap-4 mb-4">
            <div class="flex items-center gap-1">
              <span class="text-yellow-400">★</span>
              <span class="font-semibold">{{ book.avg_rating?.toFixed(2) }}</span>
            </div>
            <span class="text-gray-400 text-sm">{{ book.ratings_count?.toLocaleString() }} ratings</span>
            <span v-if="book.isbn13" class="text-gray-400 text-sm">ISBN: {{ book.isbn13 }}</span>
          </div>

          <p class="text-gray-700 text-sm leading-relaxed line-clamp-4">{{ book.description }}</p>
        </div>
      </div>
    </div>

    <!-- Similar books -->
    <section>
      <h2 class="text-xl font-bold mb-4">📖 Similar Books</h2>
      <BookGrid :books="similar" :is-loading="loadingSimilar" />
    </section>
  </div>

  <div v-else class="text-center py-16 text-gray-400">
    <div class="animate-spin text-4xl mb-4">📚</div>
    <p>Loading book...</p>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { booksApi, recommendApi } from '../services/api'
import BookGrid from '../components/BookGrid.vue'

const route = useRoute()
const book = ref(null)
const similar = ref([])
const imgError = ref(false)
const loadingSimilar = ref(false)

async function loadBook(id) {
  try {
    const res = await booksApi.getBook(id)
    book.value = res.data
    loadingSimilar.value = true
    const simRes = await recommendApi.getSimilar(id, 12)
    similar.value = simRes.data.recommendations
  } catch (e) {
    console.error('Failed to load book:', e)
  } finally {
    loadingSimilar.value = false
  }
}

onMounted(() => loadBook(route.params.id))
watch(() => route.params.id, (id) => { if (id) loadBook(id) })
</script>

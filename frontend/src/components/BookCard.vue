<template>
  <router-link :to="`/book/${book.book_id}`" class="book-card block group" @click="handleClick">

    <!-- Cover -->
    <div class="relative overflow-hidden bg-slate-100 rounded-t-xl" style="aspect-ratio:2/3">
      <img
        v-if="isValidUrl && !imgError"
        :src="book.image_url"
        :alt="book.title"
        class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
        @error="imgError = true"
        loading="lazy"
      />
      <!-- Placeholder — coloured initial -->
      <div v-else
        class="w-full h-full flex flex-col items-center justify-center p-4 relative overflow-hidden"
        :style="placeholderStyle">
        <!-- Decorative circles -->
        <div class="absolute -top-4 -right-4 w-16 h-16 rounded-full opacity-30"
          :style="{ background: placeholderAccent }"></div>
        <div class="absolute -bottom-6 -left-4 w-20 h-20 rounded-full opacity-20"
          :style="{ background: placeholderAccent }"></div>
        <!-- Initial circle -->
        <div class="w-11 h-11 rounded-full flex items-center justify-center mb-2.5 z-10 flex-shrink-0"
          :style="{ background: placeholderDark }">
          <span class="text-lg font-semibold"
            :style="{ color: placeholderLight }">
            {{ bookInitial }}
          </span>
        </div>
        <!-- Title -->
        <p class="text-center line-clamp-3 font-medium leading-snug z-10 text-xs"
          :style="{ color: placeholderDark }">
          {{ book.title }}
        </p>
      </div>

      <!-- Genre pill — bottom left of image -->
      <div v-if="book.genre"
        class="absolute bottom-2 left-2">
        <span class="text-xs font-medium px-2 py-0.5 rounded-md
          bg-black/50 text-white backdrop-blur-sm tracking-wide">
          {{ formatGenre(book.genre) }}
        </span>
      </div>

      <!-- Trending indicator — top right, subtle dot only -->
      <div v-if="isTrending"
        class="absolute top-2 right-2">
        <div class="w-6 h-6 rounded-full bg-black/40 backdrop-blur-sm
          flex items-center justify-center"
          title="Trending">
          <svg class="w-3 h-3 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5"
              d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"/>
          </svg>
        </div>
      </div>

      <!-- Hover overlay -->
      <div class="absolute inset-0 bg-black/0 group-hover:bg-black/10
        transition-colors duration-300 rounded-t-xl">
      </div>
    </div>

    <!-- Text info -->
    <div class="px-2.5 pt-2.5 pb-3">
      <!-- Title -->
      <h3 class="font-medium text-[13px] text-slate-900 line-clamp-2
        leading-snug mb-0.5 group-hover:text-primary-600 transition-colors">
        {{ book.title }}
      </h3>

      <!-- Author -->
      <p class="text-[11px] text-slate-400 truncate mb-2 leading-relaxed">
        {{ book.authors }}
      </p>

      <!-- Rating -->
      <div class="flex items-center gap-1 mb-1.5">
        <svg class="w-3 h-3 text-amber-400 fill-amber-400 flex-shrink-0"
          viewBox="0 0 20 20">
          <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"/>
        </svg>
        <span class="text-[12px] font-medium text-slate-600">
          {{ book.avg_rating?.toFixed(1) || '—' }}
        </span>
      </div>
      <!-- Why recommended -->
      <div v-if="book.reason && book.reason !== 'search' && book.reason !== 'personalized'"
        class="flex items-center gap-1 mt-0.5">
        <svg class="w-2.5 h-2.5 text-primary-400 flex-shrink-0" fill="none"
          stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
        </svg>
        <span class="text-[10px] text-slate-400 leading-tight line-clamp-1">
          {{ book.reason }}
        </span>
      </div>
    </div>

  </router-link>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  book: { type: Object, required: true },
  onCardClick: { type: Function, default: null }
})

function handleClick() {
  if (props.onCardClick) {
    props.onCardClick(props.book.book_id)
  }
}

const imgError = ref(false)

const isValidUrl = computed(() => {
  const url = props.book.image_url
  if (!url) return false
  if (url.includes('nophoto')) return false
  return url.startsWith('http')
})

// Colour palette for placeholders — 8 distinct colours keyed by first letter
const PALETTES = [
  { bg: '#E6F1FB', accent: '#B5D4F4', dark: '#185FA5', light: '#E6F1FB' }, // blue
  { bg: '#E1F5EE', accent: '#9FE1CB', dark: '#0F6E56', light: '#E1F5EE' }, // teal
  { bg: '#EEEDFE', accent: '#CECBF6', dark: '#3C3489', light: '#EEEDFE' }, // purple
  { bg: '#FAEEDA', accent: '#FAC775', dark: '#854F0B', light: '#FAEEDA' }, // amber
  { bg: '#FBEAF0', accent: '#F4C0D1', dark: '#72243E', light: '#FBEAF0' }, // pink
  { bg: '#FAECE7', accent: '#F5C4B3', dark: '#993C1D', light: '#FAECE7' }, // coral
  { bg: '#EAF3DE', accent: '#C0DD97', dark: '#3B6D11', light: '#EAF3DE' }, // green
  { bg: '#F1EFE8', accent: '#D3D1C7', dark: '#444441', light: '#F1EFE8' }, // grey
]
const bookInitial = computed(() => {
  const title = props.book.title || '?'
  return title.trim()[0].toUpperCase()
})
const palette = computed(() => {
  const code = (props.book.title || '').charCodeAt(0) || 0
  return PALETTES[code % PALETTES.length]
})
const placeholderStyle  = computed(() => ({ background: palette.value.bg }))
const placeholderAccent = computed(() => palette.value.accent)
const placeholderDark   = computed(() => palette.value.dark)
const placeholderLight  = computed(() => palette.value.light)

// Never show trending indicator — section title carries the context
// Only show if book appears in non-trending context (future use)
const isTrending = computed(() => false)

const genreMap = {
  'fiction': 'Fiction',
  'non-fiction': 'Non-Fiction',
  'romance': 'Romance',
  'fantasy, paranormal': 'Fantasy',
  'mystery, thriller, crime': 'Mystery',
  'history, historical fiction, biography': 'History',
  'children': 'Children',
  'comics, graphic': 'Comics',
  'young-adult': 'YA',
  'poetry': 'Poetry',
  'science, technology, engineering, mathematics': 'STEM',
}

function formatGenre(genre) {
  return genreMap[genre] || genre
}
</script>

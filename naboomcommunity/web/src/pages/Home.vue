<script setup>
import { ref, onMounted } from 'vue'
import { i18n } from '@/plugins/i18n'

const pages = ref([])

onMounted(async () => {
  const base = import.meta.env.VITE_API_BASE || '/api/v2'
  const locale = i18n.global.locale.value === 'af' ? 'af' : 'en'
  const res = await fetch(`${base}/pages/?locale=${locale}&limit=20&fields=title,id`)
  const data = await res.json()
  pages.value = data.items || []
})
</script>

<template>
  <div>
    <div v-for="page in pages" :key="page.id">
      {{ page.title }}
    </div>
  </div>
</template>


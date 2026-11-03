<script setup lang="ts">
withDefaults(
  defineProps<{
    size?: number
    showText?: boolean
    light?: boolean // use on dark backgrounds (footer)
  }>(),
  { size: 36, showText: true, light: false }
)

const siteName = useRuntimeConfig().public.siteName
</script>

<template>
  <span class="logo">
    <svg :width="size" :height="size" viewBox="0 0 48 48" aria-hidden="true">
      <rect width="48" height="48" rx="12" :fill="light ? '#ffffff' : '#244de4'" />
      <path
        d="M11 25 24 13.5 37 25 M16 23.5V34h16V23.5"
        fill="none"
        :stroke="light ? '#244de4' : '#ffffff'"
        stroke-width="3.5"
        stroke-linecap="round"
        stroke-linejoin="round"
      />
      <path d="m20.5 28.5 3 3 5-6" fill="none" stroke="#ff7417" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round" />
    </svg>
    <span v-if="showText" class="logo-text" :class="{ 'logo-light': light }">{{ siteName }}</span>
  </span>
</template>

<style scoped>
.logo { display: inline-flex; align-items: center; gap: 10px; }
.logo-text { font-size: 20px; font-weight: 800; letter-spacing: -0.02em; color: var(--color-text); }
.logo-light { color: #fff; }
</style>

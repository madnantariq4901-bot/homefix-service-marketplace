
<script setup lang="ts">
import {
  Facebook,
  Instagram,
  Youtube,
  Music2,
  Github,
  Linkedin,
} from 'lucide-vue-next'

import { getConfiguredSocialLinks } from '~/config/socialLinks'

const configuredLinks = getConfiguredSocialLinks()

const icons = {
  Facebook,
  Instagram,
  YouTube: Youtube,
  TikTok: Music2,
  GitHub: Github,
  LinkedIn: Linkedin,
}
</script>

<template>
  <div v-if="configuredLinks.length" class="social-links">
    <template v-for="item in configuredLinks" :key="item.name">
      <a
        :href="item.url"
        :aria-label="item.name"
        target="_blank"
        rel="noopener noreferrer"
        class="social-link"
      >
        <component :is="icons[item.name]" :size="20" />
      </a>
    </template>
  </div>
</template>

<style scoped>
.social-links {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

.social-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 42px;
  height: 42px;
  color: #a78bfa;
  border: 1px solid #3b2b59;
  border-radius: 12px;
  transition: color 0.2s, background 0.2s, border-color 0.2s;
}

a.social-link:hover {
  color: #fff;
  background: #6d28d9;
  border-color: #a78bfa;
}
</style>

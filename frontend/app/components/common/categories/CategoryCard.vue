<script setup lang="ts">
import type { Category } from "~/services/categories.service"
import { getCategoryMeta } from "~/utils/categoryMeta"

const props = defineProps<{ category: Category }>()

const currency = useRuntimeConfig().public.currencySymbol
const meta = computed(() => getCategoryMeta(props.category.name))
</script>

<template>
  <article class="category-card">
    <NuxtLink class="category-image" :to="`/categories/${category.name}`" :aria-label="`Explore ${meta.label}`">
      <img :src="meta.image" :alt="`${meta.label} service`" loading="lazy" />
      <span class="icon" aria-hidden="true">{{ meta.icon }}</span>
    </NuxtLink>
    <h2><NuxtLink :to="`/categories/${category.name}`">{{ meta.label }}</NuxtLink></h2>
    <p class="desc">{{ category.description || meta.tagline }}</p>

    <ul v-if="meta.examples.length" class="examples">
      <li v-for="item in meta.examples" :key="item">{{ item }}</li>
    </ul>

    <footer>
      <span class="rate">From <strong>{{ currency }}{{ category.base_hourly_rate }}</strong> / hour</span>
      <NuxtLink :to="`/categories/${category.name}`" class="btn btn-primary">Explore service</NuxtLink>
    </footer>
  </article>
</template>

<style scoped>
.category-card { display: flex; flex-direction: column; gap: 10px; overflow: hidden; padding: 0 0 20px; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-lg); box-shadow: var(--shadow-sm); transition: box-shadow 0.15s, transform 0.15s; }
.category-card:hover { box-shadow: var(--shadow-md); transform: translateY(-2px); }
.category-image { position: relative; display: block; height: 180px; background: var(--color-primary-soft); }
.category-image img { width: 100%; height: 100%; object-fit: cover; }
.icon { position: absolute; right: 14px; bottom: 14px; display: grid; place-items: center; width: 48px; height: 48px; color: var(--color-primary); font-size: 24px; background: #fff; border-radius: 14px; box-shadow: var(--shadow-sm); }
h2, .desc, .examples, footer { margin-right: 20px; margin-left: 20px; }
h2 { margin-top: 8px; margin-bottom: 0; font-size: 20px; }
h2 a { text-decoration: none; }
h2 a:hover { color: var(--color-primary); }
.desc { margin-top: 0; margin-bottom: 0; color: var(--color-muted); }
.examples { margin-top: 4px; margin-bottom: 8px; padding-left: 18px; color: var(--color-text); font-size: 14px; }
footer { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 12px; margin-top: auto; padding-top: 8px; }
.rate { font-size: 14px; color: var(--color-muted); }
.rate strong { color: var(--color-text); font-size: 16px; }
footer .btn { padding: 9px 14px; }
</style>

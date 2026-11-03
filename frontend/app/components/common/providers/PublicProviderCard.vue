<script setup lang="ts">
import type { PublicProvider } from "~/types/provider"
import { getCategoryMeta } from "~/utils/categoryMeta"

const props = defineProps<{ provider: PublicProvider }>()

const categoriesStore = useCategoriesStore()
const currency = useRuntimeConfig().public.currencySymbol

function rateFor(categoryId: number): number | null {
  return categoriesStore.categories.find(item => item.id === categoryId)?.base_hourly_rate ?? null
}

const initials = computed(() =>
  props.provider.full_name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((word) => word[0]!.toUpperCase())
    .join("")
)
</script>

<template>
  <article class="card">
    <header>
      <span class="avatar" aria-hidden="true">{{ initials }}</span>
      <div class="who">
        <h3>
          {{ provider.full_name }}
          <span v-if="provider.is_verified" class="verified-badge" aria-label="Marketplace verified badge">✓</span>
        </h3>
        <p class="rating">
          <template v-if="provider.rating_count">★ {{ provider.rating_avg.toFixed(1) }} <span>({{ provider.rating_count }})</span></template>
          <template v-else>New provider</template>
          <span> · {{ provider.completed_job_count }} completed job{{ provider.completed_job_count === 1 ? "" : "s" }}</span>
        </p>
      </div>
      <span class="status" :class="provider.is_available ? 'on' : 'off'">
        {{ provider.is_available ? "Available" : "Busy" }}
      </span>
    </header>

    <ul class="skills">
      <li v-for="skill in provider.skills" :key="skill.category_id">
        {{ getCategoryMeta(skill.category).icon }} {{ getCategoryMeta(skill.category).label }}
        <span v-if="skill.years_experience">· {{ skill.years_experience }} yr</span>
        <span v-if="rateFor(skill.category_id)">· from {{ currency }}{{ rateFor(skill.category_id)?.toLocaleString() }}/hr</span>
      </li>
      <li v-if="!provider.skills.length" class="none">No services listed yet</li>
    </ul>

    <footer>
      <span v-if="provider.is_verified" class="verified" title="Marketplace badge; not an automatic government ID check">✔ Marketplace badge</span>
      <NuxtLink :to="`/providers/${provider.id}`" class="btn btn-outline">View profile</NuxtLink>
    </footer>
  </article>
</template>

<style scoped>
.card { display: flex; flex-direction: column; gap: 16px; padding: 20px; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-lg); box-shadow: var(--shadow-sm); transition: box-shadow 0.15s, transform 0.15s; }
.card:hover { box-shadow: var(--shadow-md); transform: translateY(-2px); }
header { display: flex; align-items: center; gap: 12px; }
.avatar { display: grid; place-items: center; flex: none; width: 48px; height: 48px; font-weight: 700; color: var(--color-primary); background: var(--color-primary-soft); border-radius: 50%; }
.who { flex: 1; min-width: 0; }
h3 { margin: 0; font-size: 17px; }
.rating { margin: 2px 0 0; font-size: 14px; color: var(--color-muted); }
.rating span { color: var(--color-muted); }
.verified-badge { display: inline-grid; place-items: center; width: 17px; height: 17px; color: #fff; background: #1687f8; border-radius: 50%; font-size: 11px; vertical-align: 2px; }
.status { padding: 3px 10px; font-size: 12px; font-weight: 600; border-radius: 999px; }
.status.on { color: #166534; background: #dcfce7; }
.status.off { color: #475569; background: #e2e8f0; }
.skills { display: flex; flex-wrap: wrap; gap: 8px; margin: 0; padding: 0; list-style: none; }
.skills li { padding: 4px 10px; font-size: 13px; background: var(--color-page); border: 1px solid var(--color-border); border-radius: 999px; }
.skills .none { color: var(--color-muted); }
footer { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-top: auto; }
.verified { font-size: 13px; font-weight: 600; color: var(--color-teal); }
footer .btn { padding: 8px 14px; }
</style>

<script setup lang="ts">
import type { Quote } from "~/types/quote"

defineProps<{ quote: Quote; canAccept?: boolean; loading?: boolean }>()
const emit = defineEmits<{ accept: [quoteId: number] }>()
</script>

<template>
  <article class="quote-card">
    <div>
      <h2>{{ quote.provider_name }}</h2>
      <p>Quote #{{ quote.id }} · {{ quote.provider_rating_avg.toFixed(1) }} rating ({{ quote.provider_rating_count }} reviews)</p>
      <NuxtLink :to="`/providers/${quote.provider_id}`">View provider</NuxtLink>
    </div>
    <div class="quote-action">
      <strong>{{ quote.quoted_amount.toLocaleString() }}</strong>
      <button v-if="canAccept" type="button" :disabled="loading" @click="emit('accept', quote.id)">
        {{ loading ? "Accepting..." : "Accept quote" }}
      </button>
    </div>
  </article>
</template>

<style scoped>
.quote-card { display: flex; justify-content: space-between; align-items: center; gap: 16px; padding: 18px; border: 1px solid var(--color-border); border-radius: 10px; background: var(--color-surface); margin-bottom: 14px; }
h2 { margin: 0; font-size: 17px; }
p { margin: 5px 0 0; color: var(--color-muted); }
.quote-card a { display: inline-block; margin-top: 8px; font-size: 14px; }
.quote-action { display: flex; flex-direction: column; align-items: flex-end; gap: 10px; }
@media (max-width: 520px) { .quote-card { align-items: flex-start; flex-direction: column; } .quote-action { align-items: flex-start; } }
</style>

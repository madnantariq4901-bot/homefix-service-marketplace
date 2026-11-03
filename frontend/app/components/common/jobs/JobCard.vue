<script setup lang="ts">
import { Pencil, Send, Trash2 } from "lucide-vue-next"
import type { Job } from "~/types/job"

defineProps<{
  job: Job
  canEdit?: boolean
  canDelete?: boolean
  canApproach?: boolean
  approachSent?: boolean
  approaching?: boolean
  deleting?: boolean
}>()
defineEmits<{ edit: [job: Job]; approach: [job: Job]; delete: [job: Job] }>()
const currency = useRuntimeConfig().public.currencySymbol
</script>

<template>
  <article class="job-card">
    <div class="job-header">
      <h3>Job #{{ job.id }}</h3>
      <span class="status" :class="`s-${job.status}`">{{ job.status.replaceAll("_", " ") }}</span>
    </div>
    <p class="desc">{{ job.description }}</p>
    <p class="address"><span aria-hidden="true">📍</span> {{ job.address }}</p>
    <p v-if="job.customer_name" class="person"><strong>Posted by:</strong> {{ job.customer_name }}</p>
    <p v-if="job.customer_email" class="person"><strong>Customer email:</strong> <a :href="`mailto:${job.customer_email}`">{{ job.customer_email }}</a></p>
    <p v-if="job.provider_name" class="person"><strong>Service provider:</strong> {{ job.provider_name }}</p>
    <p v-if="job.provider_email" class="person"><strong>Provider email:</strong> <a :href="`mailto:${job.provider_email}`">{{ job.provider_email }}</a></p>
    <p v-if="job.quoted_amount !== null" class="amount">Quote: <strong>{{ currency }}{{ job.quoted_amount.toLocaleString() }}</strong></p>
    <NuxtLink class="view-link" :to="`/jobs/${job.id}`">View job →</NuxtLink>
    <button v-if="canEdit" class="edit-link" type="button" @click="$emit('edit', job)">
      <Pencil :size="16" aria-hidden="true" />
      Edit job
    </button>
    <button
      v-if="canApproach"
      class="approach-link"
      type="button"
      :disabled="approaching || approachSent"
      @click="$emit('approach', job)"
    >
      <Send :size="15" aria-hidden="true" />
      {{ approaching ? "Loading providers..." : approachSent ? "Provider invited" : "Approach provider" }}
    </button>
    <button
      v-if="canDelete"
      class="delete-link"
      type="button"
      :disabled="deleting"
      @click="$emit('delete', job)"
    >
      <Trash2 :size="16" aria-hidden="true" />
      {{ deleting ? "Deleting..." : "Delete job" }}
    </button>
  </article>
</template>

<style scoped>
.job-card { display: flex; flex-direction: column; gap: 6px; padding: 20px; border: 1px solid var(--color-border); border-radius: var(--radius-lg); background: var(--color-surface); box-shadow: var(--shadow-sm); transition: box-shadow .15s, transform .15s, border-color .15s; }
.job-card:hover { box-shadow: var(--shadow-md); transform: translateY(-2px); border-color: #bfdbfe; }
.job-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; }
h3 { margin: 0; font-size: 17px; }
.desc { margin: 0; }
.status { padding: 4px 10px; font-size: 12px; font-weight: 700; letter-spacing: .03em; text-transform: capitalize; white-space: nowrap; color: #334155; background: #e2e8f0; border-radius: 999px; }
.s-open, .s-posted { color: #1e40af; background: #dbeafe; }
.s-quoted { color: #92400e; background: #fef3c7; }
.s-assigned, .s-accepted, .s-en_route { color: #5b21b6; background: #ede9fe; }
.s-in_progress { color: #9a3412; background: #ffedd5; }
.s-completed { color: #166534; background: #dcfce7; }
.s-cancelled { color: #991b1b; background: #fee2e2; }
.address, .amount { margin: 0; font-size: 14px; color: var(--color-muted); }
.person { margin: 0; font-size: 13px; color: var(--color-muted); overflow-wrap: anywhere; }
.person strong { color: var(--color-text); }
.person a { color: var(--color-primary); }
.amount strong { color: var(--color-text); }
.view-link { margin-top: 6px; font-weight: 600; color: var(--color-primary); text-decoration: none; }
.view-link:hover { text-decoration: underline; }
.edit-link { display: inline-flex; align-items: center; align-self: flex-start; gap: 7px; margin-top: 4px; padding: 6px 0; color: var(--color-primary); background: transparent; border: 0; box-shadow: none; font-weight: 600; }
.edit-link:hover:not(:disabled) { background: transparent; box-shadow: none; transform: none; }
.approach-link { display: inline-flex; align-items: center; align-self: flex-start; gap: 7px; margin-top: 4px; padding: 6px 0; color: #0b765e; background: transparent; border: 0; box-shadow: none; font-weight: 600; }
.approach-link:hover:not(:disabled) { color: #075c49; background: transparent; box-shadow: none; transform: none; }
.approach-link:disabled { cursor: default; opacity: .7; }
.delete-link { display: inline-flex; align-items: center; align-self: flex-start; gap: 7px; margin-top: 4px; padding: 6px 0; color: #b42318; background: transparent; border: 0; box-shadow: none; font-weight: 600; }
.delete-link:hover:not(:disabled) { color: #8f1d14; background: transparent; box-shadow: none; transform: none; }
.delete-link:disabled { cursor: wait; opacity: .65; }
</style>

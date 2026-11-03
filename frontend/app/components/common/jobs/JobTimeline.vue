<script setup lang="ts">
import type { JobStatus } from "~/types/job"

const props = defineProps<{ status: JobStatus }>()

const steps: { key: JobStatus; label: string }[] = [
  { key: "requested", label: "Requested" },
  { key: "quoted", label: "Quoted" },
  { key: "accepted", label: "Accepted" },
  { key: "en_route", label: "On the way" },
  { key: "in_progress", label: "In progress" },
  { key: "completed", label: "Completed" },
]

const currentIndex = computed(() => steps.findIndex(step => step.key === props.status))
const isDone = (index: number) => props.status === "completed" || index < currentIndex.value
</script>

<template>
  <div v-if="status === 'cancelled'" class="timeline-cancelled" role="status">This job was cancelled.</div>
  <ol v-else class="timeline" aria-label="Job progress">
    <li
      v-for="(step, index) in steps"
      :key="step.key"
      :class="{ done: isDone(index), current: index === currentIndex && status !== 'completed' }"
    >
      <span class="dot">{{ isDone(index) ? "✓" : index + 1 }}</span>
      <span class="label">{{ step.label }}</span>
    </li>
  </ol>
</template>

<style scoped>
.timeline { display: flex; margin: 20px 0; padding: 0 0 6px; list-style: none; overflow-x: auto; }
.timeline li { position: relative; display: flex; flex: 1 0 86px; flex-direction: column; align-items: center; gap: 7px; color: var(--color-muted); font-size: 13px; text-align: center; }
.timeline li:not(:last-child)::after { content: ""; position: absolute; top: 15px; left: calc(50% + 19px); width: calc(100% - 38px); height: 2px; background: var(--color-border); }
.timeline li.done:not(:last-child)::after { background: var(--color-primary); }
.dot { display: grid; place-items: center; width: 30px; height: 30px; background: var(--color-surface); border: 2px solid var(--color-border); border-radius: 50%; font-size: 13px; font-weight: 700; }
.done .dot { color: #fff; background: var(--color-primary); border-color: var(--color-primary); }
.current .dot { color: var(--color-primary); border-color: var(--color-primary); box-shadow: 0 0 0 4px var(--color-primary-soft); }
.current .label { color: var(--color-text); font-weight: 700; }
.timeline-cancelled { margin: 18px 0; padding: 12px 16px; color: var(--color-danger); background: #fef2f2; border: 1px solid #fecaca; border-radius: var(--radius); font-weight: 600; }
</style>

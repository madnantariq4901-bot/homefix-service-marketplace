<script setup lang="ts">
import { Film, Image as ImageIcon } from "lucide-vue-next"
import { jobsService } from "~/services/jobs.service"
import type { JobAttachment } from "~/types/job"

const props = defineProps<{ jobId: number; attachments: JobAttachment[] }>()
const fileUrls = ref<Record<number, string>>({})
const failedIds = ref<number[]>([])

onMounted(async () => {
  const results = await Promise.all(props.attachments.map(async (attachment) => {
    try {
      const blob = await jobsService.getAttachmentFile(props.jobId, attachment.id)
      return { id: attachment.id, url: URL.createObjectURL(blob) }
    } catch {
      failedIds.value.push(attachment.id)
      return null
    }
  }))
  fileUrls.value = Object.fromEntries(results.filter(Boolean).map(result => [result!.id, result!.url]))
})

onBeforeUnmount(() => {
  Object.values(fileUrls.value).forEach(URL.revokeObjectURL)
})

function formatSize(bytes: number) {
  return bytes >= 1024 * 1024
    ? `${(bytes / (1024 * 1024)).toFixed(1)} MB`
    : `${Math.max(1, Math.round(bytes / 1024))} KB`
}
</script>

<template>
  <section class="job-attachments" aria-labelledby="job-attachments-title">
    <h2 id="job-attachments-title">Job photos and videos</h2>
    <div class="attachment-grid">
      <article v-for="attachment in attachments" :key="attachment.id" class="attachment-item">
        <p v-if="failedIds.includes(attachment.id)" class="attachment-unavailable">This file couldn’t be loaded.</p>
        <template v-else-if="fileUrls[attachment.id]">
          <video v-if="attachment.media_type.startsWith('video/')" :src="fileUrls[attachment.id]" controls preload="metadata" />
          <img v-else :src="fileUrls[attachment.id]" :alt="attachment.original_name" loading="lazy" />
        </template>
        <div v-else class="attachment-loading" aria-label="Loading attachment">
          <Film v-if="attachment.media_type.startsWith('video/')" :size="22" aria-hidden="true" />
          <ImageIcon v-else :size="22" aria-hidden="true" />
        </div>
        <p class="attachment-name" :title="attachment.original_name">{{ attachment.original_name }} <span>{{ formatSize(attachment.size_bytes) }}</span></p>
      </article>
    </div>
  </section>
</template>

<style scoped>
.job-attachments { margin-top: 24px; padding-top: 20px; border-top: 1px solid var(--color-border); }
.job-attachments h2 { margin: 0 0 13px; font-size: 18px; }
.attachment-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 12px; }
.attachment-item { min-width: 0; overflow: hidden; background: var(--color-page); border: 1px solid var(--color-border); border-radius: 8px; }
.attachment-item img, .attachment-item video, .attachment-loading, .attachment-unavailable { display: grid; width: 100%; aspect-ratio: 4 / 3; object-fit: cover; background: var(--color-page); }
.attachment-loading { place-items: center; color: var(--color-muted); }
.attachment-unavailable { place-items: center; margin: 0; padding: 10px; color: var(--color-muted); font-size: 12px; text-align: center; }
.attachment-name { display: flex; justify-content: space-between; gap: 8px; overflow: hidden; margin: 0; padding: 8px; font-size: 11px; }
.attachment-name { white-space: nowrap; text-overflow: ellipsis; }
.attachment-name span { flex: 0 0 auto; color: var(--color-muted); }
</style>

<script setup lang="ts">
import { categoriesService } from "~/services/categories.service"
import type { Category } from "~/types/category"

definePageMeta({ middleware: "auth" })
useHead({ title: "Edit job" })

const route = useRoute()
const jobsStore = useJobsStore()
const categories = ref<Category[]>([])
const loading = ref(true)
const saving = ref(false)
const error = ref("")
const message = ref("")
const jobId = Number(route.params.id)
const draft = reactive({
  category_id: 0,
  description: "",
  address: "",
  lat: null as number | null,
  lng: null as number | null,
})

onMounted(async () => {
  loading.value = true
  error.value = ""
  try {
    const [job] = await Promise.all([
      jobsStore.fetchJob(jobId),
      categoriesService.getCategories().then((items) => { categories.value = items }),
    ])
    draft.category_id = job.category_id
    draft.description = job.description
    draft.address = job.address
    draft.lat = job.lat
    draft.lng = job.lng
  } catch (err: any) {
    error.value = err?.data?.detail || jobsStore.error || "Unable to load this job."
  } finally {
    loading.value = false
  }
})

async function saveChanges() {
  saving.value = true
  error.value = ""
  message.value = ""
  try {
    await jobsStore.updateJobDetails(jobId, {
      category_id: draft.category_id,
      description: draft.description.trim(),
      address: draft.address.trim(),
      lat: draft.lat,
      lng: draft.lng,
    })
    message.value = "Job details updated."
  } catch (err: any) {
    error.value = err?.data?.detail || jobsStore.error || "Unable to update job details."
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <main class="edit-page">
    <header class="page-heading">
      <div><p class="eyebrow">Job #{{ jobId }}</p><h1>Edit job details</h1></div>
      <NuxtLink class="btn btn-outline" :to="`/jobs/${jobId}`">Back to job</NuxtLink>
    </header>
    <AppAlert v-if="error" type="error">{{ error }}</AppAlert>
    <AppAlert v-if="message" type="success">{{ message }}</AppAlert>
    <AppLoader v-if="loading" />
    <form v-else class="edit-form" @submit.prevent="saveChanges">
      <label>Service
        <select v-model.number="draft.category_id" required>
          <option v-for="category in categories" :key="category.id" :value="category.id">{{ category.name.replaceAll("_", " ") }}</option>
        </select>
      </label>
      <label>Description
        <textarea v-model="draft.description" minlength="3" maxlength="2000" required rows="4" />
      </label>
      <label>Address
        <input v-model="draft.address" minlength="3" maxlength="500" required />
      </label>
      <div class="coordinate-fields">
        <label>Latitude
          <input v-model.number="draft.lat" type="number" min="-90" max="90" step="any" />
        </label>
        <label>Longitude
          <input v-model.number="draft.lng" type="number" min="-180" max="180" step="any" />
        </label>
      </div>
      <p class="form-note">Leave both coordinates blank to clear the job location pin.</p>
      <div class="form-actions">
        <button class="btn btn-primary" type="submit" :disabled="saving">{{ saving ? "Saving..." : "Save changes" }}</button>
        <NuxtLink class="btn btn-outline" :to="`/jobs/${jobId}`">Cancel</NuxtLink>
      </div>
    </form>
  </main>
</template>

<style scoped>
.edit-page { width: min(820px, 100% - 32px); margin: 0 auto; padding: 32px 0 56px; }
.page-heading { display: flex; justify-content: space-between; align-items: center; gap: 18px; margin-bottom: 22px; }
.page-heading h1 { margin: 3px 0 0; font-size: 30px; }
.eyebrow { margin: 0; color: var(--color-primary); font-size: 12px; font-weight: 700; text-transform: uppercase; }
.edit-form { display: grid; gap: 16px; max-width: none; padding: 22px; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: 8px; }
label { display: grid; gap: 7px; font-size: 13px; font-weight: 700; }
input, select, textarea { width: 100%; }
textarea { resize: vertical; }
.coordinate-fields { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
.form-note { margin: -8px 0 0; color: var(--color-muted); font-size: 12px; }
.form-actions { display: flex; flex-wrap: wrap; gap: 10px; }
@media (max-width: 560px) { .page-heading { align-items: flex-start; flex-direction: column; } .coordinate-fields { grid-template-columns: 1fr; } }
</style>
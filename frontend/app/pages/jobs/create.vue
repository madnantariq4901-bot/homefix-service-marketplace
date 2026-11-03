<script setup lang="ts">
import { providersService } from "~/services/provider.service"
import type { PublicProvider } from "~/types/provider"

definePageMeta({ middleware: ["auth", "role"], requiredRole: ["customer", "admin"] })

const route = useRoute()
const jobsStore = useJobsStore()
const categoriesStore = useCategoriesStore()
const description = ref("")
const categoryId = ref<number | null>(null)
const address = ref("")
const city = ref("")
const lat = ref<number | null>(null)
const lng = ref<number | null>(null)
const error = ref("")
const relatedProviders = ref<PublicProvider[]>([])
const providersLoading = ref(false)
const preferredProviderId = ref<number | null>(null)
const selectedFiles = ref<File[]>([])
const createdJobId = ref<number | null>(null)
const uploadingAttachments = ref(false)
const maxFileBytes = 20 * 1024 * 1024
const maxTotalBytes = 50 * 1024 * 1024
const maxFiles = 5

async function loadRelatedProviders(requestedProviderId?: number) {
  const category = categoriesStore.categories.find(item => item.id === categoryId.value)
  if (!category) {
    relatedProviders.value = []
    preferredProviderId.value = null
    return
  }

  providersLoading.value = true
  try {
    relatedProviders.value = await providersService.getPublicProviders({ category: category.name, limit: 100 })
    preferredProviderId.value = requestedProviderId && relatedProviders.value.some(item => item.id === requestedProviderId)
      ? requestedProviderId
      : null
  } catch {
    relatedProviders.value = []
    preferredProviderId.value = null
  } finally {
    providersLoading.value = false
  }
}

onMounted(async () => {
  try {
    await categoriesStore.fetchCategories()
    const requestedCategoryId = Number(route.query.category)
    const requestedCategory = Number.isInteger(requestedCategoryId)
      ? categoriesStore.categories.find(category => category.id === requestedCategoryId)
      : undefined
    if (requestedCategory) {
      categoryId.value = requestedCategory.id
    } else if (categoriesStore.categories.length && categoryId.value === null) {
      categoryId.value = categoriesStore.categories[0].id
    }
    const requestedProviderId = Number(route.query.provider)
    await loadRelatedProviders(Number.isInteger(requestedProviderId) && requestedProviderId > 0 ? requestedProviderId : undefined)
  } catch {
    error.value = categoriesStore.error || "Unable to load service categories."
  }
})

function onPicked(p: { address: string; city: string; latitude: number; longitude: number }) {
  address.value = p.address
  city.value = p.city
  lat.value = p.latitude
  lng.value = p.longitude
}

function onCategoryChanged() {
  preferredProviderId.value = null
  void loadRelatedProviders()
}

function onLocationCleared() {
  lat.value = null
  lng.value = null
}

function onFilesSelected(event: Event) {
  error.value = ""
  const input = event.target as HTMLInputElement
  const files = Array.from(input.files ?? [])
  if (files.length > maxFiles) {
    error.value = "Choose up to 5 photos or videos."
    input.value = ""
    return
  }
  if (files.some(file => file.size > maxFileBytes) || files.reduce((total, file) => total + file.size, 0) > maxTotalBytes) {
    error.value = "Each file must be 20 MB or smaller, and all files together must be 50 MB or smaller."
    input.value = ""
    return
  }
  const acceptedTypes = ["image/jpeg", "image/png", "image/webp", "video/mp4", "video/quicktime", "video/webm"]
  if (files.some(file => !acceptedTypes.includes(file.type))) {
    error.value = "Choose JPEG, PNG, or WebP photos, or MP4, MOV, or WebM videos."
    input.value = ""
    return
  }
  selectedFiles.value = files
}

function removeFile(index: number) {
  selectedFiles.value.splice(index, 1)
}

async function uploadAttachments(jobId: number) {
  if (!selectedFiles.value.length) return true
  uploadingAttachments.value = true
  try {
    await jobsStore.uploadAttachments(jobId, selectedFiles.value)
    selectedFiles.value = []
    return true
  } catch (err: any) {
    error.value = err?.data?.detail || "Your job was posted, but the attachments could not be uploaded. Retry the upload below."
    return false
  } finally {
    uploadingAttachments.value = false
  }
}

async function createJob() {
  error.value = ""
  if (createdJobId.value !== null) {
    if (await uploadAttachments(createdJobId.value)) await navigateTo(`/jobs/${createdJobId.value}`)
    return
  }
  if (!categoryId.value || !description.value.trim() || !address.value.trim()) {
    error.value = "Complete the category, description, and location fields."
    return
  }
  if (lat.value === null || lng.value === null) {
    error.value = "Choose the job location on the map (search an address or click the map)."
    return
  }

  try {
    const job = await jobsStore.createJob({
      category_id: categoryId.value,
      ...(preferredProviderId.value !== null ? { preferred_provider_id: preferredProviderId.value } : {}),
      description: description.value.trim(),
      address: address.value.trim(),
      lat: lat.value,
      lng: lng.value,
    })
    createdJobId.value = job.id
    if (!(await uploadAttachments(job.id))) return
    await navigateTo(`/jobs/${job.id}`)
  } catch (err: any) {
    error.value = err?.data?.detail || jobsStore.error || "Unable to create job."
  }
}
</script>

<template>
  <main class="page">
    <section class="form-card">
      <h1>Post a job</h1>
      <form @submit.prevent="createJob">
        <label>
          Service category
          <select v-model.number="categoryId" required :disabled="createdJobId !== null" @change="onCategoryChanged">
            <option v-for="category in categoriesStore.categories" :key="category.id" :value="category.id">
              {{ category.name }}
            </option>
          </select>
        </label>
        <label>
          Preferred provider (optional)
          <select v-model.number="preferredProviderId" :disabled="createdJobId !== null || providersLoading || !relatedProviders.length">
            <option :value="null">Open to any matching provider</option>
            <option v-for="provider in relatedProviders" :key="provider.id" :value="provider.id">
              {{ provider.full_name }} · {{ provider.completed_job_count }} completed jobs{{ provider.is_available ? " · Available" : "" }}
            </option>
          </select>
          <small v-if="providersLoading" class="hint">Finding providers for this service…</small>
          <small v-else-if="!relatedProviders.length" class="hint">No listed providers are available for this service yet. Your request can still be posted openly.</small>
          <small v-else class="hint">A selected provider is invited first; the job is not assigned until you accept their quote.</small>
        </label>
        <label class="description-field">
          Description
          <textarea v-model="description" minlength="3" maxlength="2000" rows="5" required :disabled="createdJobId !== null" placeholder="Describe the service you need" />
          <span class="attachment-picker">
            <span class="attachment-label">Add photos or videos <small>(optional)</small></span>
            <input
              id="job-attachments"
              type="file"
              accept="image/jpeg,image/png,image/webp,video/mp4,video/quicktime,video/webm"
              multiple
              :disabled="createdJobId !== null"
              @change="onFilesSelected"
            />
            <small class="hint">Up to 5 files · 20 MB each · 50 MB total. The written description is required.</small>
            <ul v-if="selectedFiles.length" class="selected-files">
              <li v-for="(file, index) in selectedFiles" :key="`${file.name}-${file.lastModified}`">
                <span>{{ file.name }} · {{ (file.size / (1024 * 1024)).toFixed(1) }} MB</span>
                <button type="button" class="remove-file" :disabled="createdJobId !== null" :aria-label="`Remove ${file.name}`" @click="removeFile(index)">Remove</button>
              </li>
            </ul>
          </span>
        </label>

        <div class="map-block">
          <span class="map-title">Job location</span>
          <ClientOnly>
            <AddressMapPicker @picked="onPicked" @cleared="onLocationCleared" />
          </ClientOnly>
        </div>

        <AppAlert v-if="error" type="error">{{ error }}</AppAlert>
        <AppAlert v-if="categoriesStore.error" type="error">{{ categoriesStore.error }}</AppAlert>
        <button type="submit" :disabled="jobsStore.loading || uploadingAttachments || categoriesStore.loading || !categoriesStore.categories.length">
          {{ jobsStore.loading ? "Posting..." : uploadingAttachments ? "Uploading attachments..." : createdJobId !== null ? "Retry upload and open job" : "Post a job" }}
        </button>
      </form>
    </section>
  </main>
</template>

<style scoped>
.page { padding: 28px 16px; }
.form-card { max-width: 720px; margin: 0 auto; padding: 26px; border: 1px solid var(--color-border); border-radius: 10px; background: var(--color-surface); }
h1 { margin-top: 0; }
form, label { display: flex; flex-direction: column; gap: 8px; }
form { gap: 16px; }
label, .map-title { font-size: 14px; font-weight: 600; }
.map-block { display: flex; flex-direction: column; gap: 8px; }
.description-field { gap: 10px; }
.attachment-picker { display: grid; gap: 7px; padding: 11px; background: var(--color-page); border: 1px solid var(--color-border); border-radius: 6px; }
.attachment-label { font-size: 13px; font-weight: 700; }
.attachment-label small { color: var(--color-muted); font-weight: 400; }
.attachment-picker input[type="file"] { min-height: 0; padding: 6px; background: var(--color-surface); font-size: 12px; }
.hint { margin: 0; font-size: 13px; color: var(--color-muted); }
.selected-files { display: grid; gap: 7px; margin: -4px 0 0; padding: 0; list-style: none; }
.selected-files li { display: flex; justify-content: space-between; align-items: center; gap: 12px; padding: 8px 10px; background: var(--color-page); border: 1px solid var(--color-border); border-radius: 6px; font-size: 12px; }
.remove-file { min-height: 0; padding: 4px 7px; color: var(--color-danger); background: transparent; border: 0; box-shadow: none; font-size: 12px; }
.remove-file:hover:not(:disabled) { background: transparent; box-shadow: none; transform: none; }
textarea { resize: vertical; }
</style>
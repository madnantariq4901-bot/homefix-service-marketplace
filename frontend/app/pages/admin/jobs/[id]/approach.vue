<script setup lang="ts">
import { jobsService } from "~/services/jobs.service"
import { providersService } from "~/services/provider.service"
import type { ProviderAdminDirectoryItem } from "~/types/provider"

definePageMeta({ middleware: ["auth", "role"], requiredRole: "admin" })
useHead({ title: "Approach provider" })

const route = useRoute()
const jobsStore = useJobsStore()
const jobId = Number(route.params.id)
const providers = ref<ProviderAdminDirectoryItem[]>([])
const selectedProviderId = ref<number | null>(null)
const loading = ref(true)
const sending = ref(false)
const error = ref("")
const success = ref("")
const invitedProviderIds = ref<number[]>([])
const job = computed(() => jobsStore.currentJob)
const listedProviders = computed(() => providers.value)

onMounted(async () => {
  loading.value = true
  error.value = ""
  try {
    const [, directory] = await Promise.all([
      jobsStore.fetchJob(jobId),
      providersService.getProviders(),
    ])
    providers.value = directory
    if (!job.value || !["requested", "quoted"].includes(job.value.status) || job.value.provider_id !== null) {
      error.value = "This job is no longer accepting provider invitations."
    } else if (!listedProviders.value.length) {
      error.value = "No provider accounts are registered yet."
    }
  } catch (err: any) {
    error.value = err?.data?.detail || jobsStore.error || "Unable to load this job or provider list."
  } finally {
    loading.value = false
  }
})

async function sendInvitation() {
  if (selectedProviderId.value === null) return
  const provider = listedProviders.value.find(item => item.id === selectedProviderId.value)
  if (!provider || !window.confirm(`Invite ${provider.full_name} to consider job #${jobId}?`)) return

  sending.value = true
  error.value = ""
  success.value = ""
  try {
    await jobsService.approachProvider(jobId, provider.id)
    invitedProviderIds.value.push(provider.id)
    success.value = `${provider.full_name} was invited. They can review the job and quote if available and eligible.`
    selectedProviderId.value = null
  } catch (err: any) {
    error.value = err?.data?.detail || "Unable to invite this provider."
  } finally {
    sending.value = false
  }
}
</script>

<template>
  <main class="approach-page">
    <header class="page-heading">
      <div><p class="eyebrow">Admin outreach · Job #{{ jobId }}</p><h1>Approach a provider</h1></div>
      <NuxtLink class="btn btn-outline" to="/jobs">Back to jobs</NuxtLink>
    </header>
    <AppLoader v-if="loading" />
    <template v-else>
      <AppAlert v-if="error" type="error">{{ error }}</AppAlert>
      <AppAlert v-if="success" type="success">{{ success }}</AppAlert>
      <section v-if="job" class="job-summary">
        <div><p class="eyebrow">{{ job.status.replaceAll("_", " ") }}</p><h2>{{ job.description }}</h2><p>{{ job.address }}</p></div>
        <p class="service-tag">Service #{{ job.category_id }}</p>
      </section>
      <form v-if="job && listedProviders.length && ['requested', 'quoted'].includes(job.status) && job.provider_id === null" class="approach-form" @submit.prevent="sendInvitation">
        <label>Registered provider
          <select v-model.number="selectedProviderId" required>
            <option :value="null" disabled>Select a provider</option>
            <option
              v-for="provider in listedProviders"
              :key="provider.id"
              :value="provider.id"
              :disabled="invitedProviderIds.includes(provider.id)"
            >
              {{ provider.full_name }} · {{ provider.completed_job_count }} completed · {{ provider.is_available ? "Available" : "Unavailable" }} · {{ provider.skills.some(skill => skill.category_id === job?.category_id) ? "Has this skill" : "No listed skill" }}
            </option>
          </select>
        </label>
        <p class="form-note">This sends an invitation only. It does not assign the provider or accept a quote. Providers without this service listed can still review the job, but must add the skill and meet availability and identity checks before quoting.</p>
        <div class="form-actions">
          <button class="btn btn-primary" type="submit" :disabled="sending || selectedProviderId === null">{{ sending ? "Sending..." : "Send invitation" }}</button>
          <NuxtLink class="btn btn-outline" to="/jobs">Cancel</NuxtLink>
        </div>
      </form>
    </template>
  </main>
</template>

<style scoped>
.approach-page { width: min(820px, 100% - 32px); margin: 0 auto; padding: 32px 0 56px; }
.page-heading { display: flex; justify-content: space-between; align-items: center; gap: 18px; margin-bottom: 22px; }
.page-heading h1 { margin: 3px 0 0; font-size: 30px; }
.eyebrow { margin: 0; color: var(--color-primary); font-size: 12px; font-weight: 700; text-transform: uppercase; }
.job-summary { display: flex; justify-content: space-between; align-items: flex-start; gap: 18px; margin-bottom: 16px; padding: 18px; background: var(--color-page); border-left: 4px solid var(--color-primary); }
.job-summary h2 { margin: 5px 0; font-size: 20px; }
.job-summary p { margin: 0; color: var(--color-muted); }
.service-tag { flex: 0 0 auto; padding: 6px 9px; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: 6px; font-size: 12px; }
.approach-form { display: grid; gap: 16px; max-width: none; padding: 22px; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: 8px; }
label { display: grid; gap: 7px; font-size: 13px; font-weight: 700; }
select { width: 100%; }
.form-note { margin: -5px 0 0; color: var(--color-muted); font-size: 13px; line-height: 1.5; }
.form-actions { display: flex; flex-wrap: wrap; gap: 10px; }
@media (max-width: 560px) { .page-heading, .job-summary { align-items: flex-start; flex-direction: column; } }
</style>
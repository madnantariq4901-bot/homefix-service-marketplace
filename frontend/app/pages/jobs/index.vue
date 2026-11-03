<script setup lang="ts">
import type { Job } from "~/types/job"

definePageMeta({ middleware: "auth" })

const jobsStore = useJobsStore()
const authStore = useAuthStore()
const providersStore = useProvidersStore()
const loadError = ref("")
const deletingJobId = ref<number | null>(null)

const statusFilter = ref<"all" | "active" | "completed" | "cancelled">("all")
const search = ref("")
const filters = [
  { key: "all", label: "All" },
  { key: "active", label: "Active" },
  { key: "completed", label: "Completed" },
  { key: "cancelled", label: "Cancelled" },
] as const

const filteredJobs = computed(() => {
  const term = search.value.trim().toLowerCase()
  return jobsStore.jobs.filter((job) => {
    if (statusFilter.value === "active" && ["completed", "cancelled"].includes(job.status)) return false
    if (statusFilter.value === "completed" && job.status !== "completed") return false
    if (statusFilter.value === "cancelled" && job.status !== "cancelled") return false
    if (!term) return true
    return `${job.id} ${job.description} ${job.address} ${job.status}`.toLowerCase().includes(term)
  })
})

const opportunityEmptyMessage = computed(() => {
  if (authStore.user?.role === "admin") {
    return "There are no unassigned customer jobs waiting for quotes right now."
  }
  if (!providersStore.provider?.skills.length) {
    return "Add a service skill to your profile to see matching customer jobs."
  }
  return "There are no open customer jobs in your skill categories right now. Check back soon."
})

function canEditJob(job: Job) {
  const user = authStore.user
  if (!user) return false
  if (user.role === "admin") return true
  if (user.role === "customer") return job.customer_id === user.id
  return user.role === "provider" && job.provider_id !== null && job.provider_id === providersStore.provider?.id
}

function openEdit(job: Job) {
  return navigateTo(`/jobs/${job.id}/edit`)
}

function openApproach(job: Job) {
  return navigateTo(`/admin/jobs/${job.id}/approach`)
}

async function deleteJob(jobId: number) {
  if (!window.confirm(`Permanently delete job #${jobId}? This cannot be undone.`)) return

  deletingJobId.value = jobId
  loadError.value = ""
  try {
    await jobsStore.deleteJob(jobId)
  } catch (err: any) {
    loadError.value = err?.data?.detail || jobsStore.error || "Unable to delete job."
  } finally {
    deletingJobId.value = null
  }
}

onMounted(async () => {
  loadError.value = ""
  try {
    if (!authStore.user) await authStore.loadCurrentUser()
    if (authStore.user?.role === "provider") {
      await Promise.all([
        jobsStore.fetchMyJobs(),
        jobsStore.fetchAvailableJobs(),
        providersStore.fetchMyProfile(),
      ])
    } else if (authStore.user?.role === "admin") {
      await Promise.all([
        jobsStore.fetchMyJobs(),
        jobsStore.fetchAvailableJobs(),
      ])
    } else {
      await jobsStore.fetchMyJobs()
    }
  } catch (err: any) {
    loadError.value = err?.data?.detail || jobsStore.error || providersStore.error || "Unable to load jobs."
  }
})
</script>

<template>
  <main class="jobs-page">
    <section class="jobs-hero">
      <div>
        <p class="eyebrow">{{ authStore.user?.role === "provider" ? "Your work and opportunities" : "Your home-service activity" }}</p>
        <h1>{{ authStore.user?.role === "provider" ? "Jobs that fit your skills." : "Every request, all in one place." }}</h1>
        <p>{{ authStore.user?.role === "provider" ? "Keep track of active work and find matching requests from local customers." : "Follow your requests from the first quote through to completion." }}</p>
        <NuxtLink v-if="authStore.user?.role === 'customer'" class="btn btn-accent" to="/jobs/create">Start a new request <span aria-hidden="true">→</span></NuxtLink>
        <NuxtLink v-else class="btn btn-accent" to="/categories">Explore services <span aria-hidden="true">→</span></NuxtLink>
      </div>
      <img
        src="https://images.unsplash.com/photo-1621905251918-48416bd8575a?auto=format&fit=crop&w=1100&q=85"
        alt="A service professional completing work at home"
      />
    </section>

    <AppAlert v-if="loadError || jobsStore.error" type="error">{{ loadError || jobsStore.error }}</AppAlert>
    <AppLoader v-if="jobsStore.loading" />

    <section v-else>
      <div class="list-heading">
        <div><p class="eyebrow section-eyebrow">Job activity</p><h2>{{ authStore.user?.role === "provider" ? "Assigned and quoted jobs" : authStore.user?.role === "admin" ? "All customer jobs" : "Your requests" }}</h2></div>
        <span class="count">{{ jobsStore.jobs.length }} {{ jobsStore.jobs.length === 1 ? "job" : "jobs" }}</span>
      </div>
      <div v-if="jobsStore.jobs.length" class="job-filters">
        <div class="tabs" role="tablist">
          <button
            v-for="item in filters"
            :key="item.key"
            type="button"
            :class="{ active: statusFilter === item.key }"
            @click="statusFilter = item.key"
          >{{ item.label }}</button>
        </div>
        <input v-model="search" type="search" placeholder="Search by job number, description or address" />
      </div>
      <div v-if="!jobsStore.jobs.length" class="empty-state">
        <span class="empty-icon" aria-hidden="true">⌂</span>
        <div><h3>{{ authStore.user?.role === "provider" ? "No active jobs yet" : "Your requests will appear here" }}</h3><p>{{ authStore.user?.role === "provider" ? "Check the matching opportunities below for new work." : "Choose a service and describe what you need to get started." }}</p></div>
        <NuxtLink v-if="authStore.user?.role === 'customer'" to="/categories" class="btn btn-outline">Browse services</NuxtLink>
      </div>
      <p v-else-if="!filteredJobs.length" class="muted">No jobs match your filters.</p>
      <div v-else class="jobs-list">
        <JobCard
          v-for="job in filteredJobs"
          :key="job.id"
          :job="job"
          :can-edit="canEditJob(job)"
          :can-delete="authStore.user?.role === 'admin'"
          :can-approach="authStore.user?.role === 'admin' && ['requested', 'quoted'].includes(job.status) && job.provider_id === null"
          :deleting="deletingJobId === job.id"
          @edit="openEdit"
          @approach="openApproach"
          @delete="deleteJob(job.id)"
        />
      </div>

      <template v-if="authStore.user?.role === 'provider' || authStore.user?.role === 'admin'">
        <div class="list-heading opportunities-heading">
          <div><p class="eyebrow section-eyebrow">{{ authStore.user?.role === "admin" ? "Marketplace overview" : "Made for your skills" }}</p><h2>{{ authStore.user?.role === "admin" ? "Available open jobs" : "Available opportunities" }}</h2></div>
          <span class="count">{{ jobsStore.availableJobs.length }} available</span>
        </div>
        <div v-if="!jobsStore.availableJobs.length" class="opportunities-empty">
          <p class="muted">{{ opportunityEmptyMessage }}</p>
          <NuxtLink v-if="!providersStore.provider?.skills.length" to="/providers" class="text-link">Add service skills →</NuxtLink>
        </div>
        <div v-else class="jobs-list">
          <JobCard v-for="job in jobsStore.availableJobs" :key="job.id" :job="job" />
        </div>
      </template>
    </section>
  </main>
</template>

<style scoped>
.jobs-page { padding: 28px; max-width: 1200px; margin: 0 auto; }
.jobs-hero { display: grid; grid-template-columns: 1fr .85fr; align-items: center; gap: 34px; overflow: hidden; margin: 0 0 36px; padding: clamp(24px, 4vw, 40px); color: #fff; background: var(--color-dark); border-radius: 18px; }
.jobs-hero h1 { max-width: 590px; margin: 0 0 12px; color: #fff; font-size: clamp(34px, 4vw, 48px); line-height: 1.08; }
.jobs-hero p:not(.eyebrow) { max-width: 520px; margin: 0 0 20px; color: #dbe5f2; }
.eyebrow { margin: 0 0 9px; color: #ffc48d; font-size: 12px; font-weight: 700; letter-spacing: .15em; text-transform: uppercase; }
.section-eyebrow { color: var(--color-primary); }
.jobs-hero img { width: 100%; height: 230px; object-fit: cover; border-radius: 14px; }
.list-heading { display: flex; justify-content: space-between; align-items: end; gap: 16px; margin-bottom: 18px; }
.list-heading h2 { margin: 0; }
.count { padding: 6px 11px; color: var(--color-primary); background: var(--color-primary-soft); border-radius: 999px; font-size: 13px; font-weight: 700; white-space: nowrap; }
.opportunities-heading { margin-top: 38px; }
.muted { color: var(--color-muted); }
.empty-state { display: flex; align-items: center; gap: 16px; padding: 24px; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-lg); }
.empty-icon { display: grid; place-items: center; flex: 0 0 48px; width: 48px; height: 48px; color: var(--color-primary); background: var(--color-primary-soft); border-radius: 14px; font-size: 24px; }
.empty-state div { flex: 1; }
.empty-state h3 { margin: 0 0 5px; }
.empty-state p { margin: 0; color: var(--color-muted); }
.jobs-list { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; }
@media (max-width: 760px) { .jobs-page { padding: 18px; } .jobs-hero { grid-template-columns: 1fr; } .jobs-hero img { height: 200px; } .jobs-list { grid-template-columns: 1fr; } }
@media (max-width: 520px) { .list-heading { align-items: flex-start; flex-direction: column; } .empty-state { align-items: flex-start; flex-direction: column; } }
.job-filters { display: flex; flex-wrap: wrap; align-items: center; gap: 12px; margin-bottom: 18px; }
.tabs { display: flex; flex-wrap: wrap; gap: 8px; }
.tabs button { min-height: 0; padding: 7px 14px; color: var(--color-text); background: var(--color-surface); border: 1px solid var(--color-border); border-radius: 999px; box-shadow: none; font-weight: 600; }
.tabs button:hover:not(:disabled) { background: var(--color-primary-soft); box-shadow: none; transform: none; }
.tabs button.active { color: #fff; background: var(--color-primary); border-color: var(--color-primary); }
.job-filters input { flex: 1 1 240px; max-width: 360px; }
.coordinate-fields { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
.form-note { margin: -8px 0 0; color: var(--color-muted); font-size: 12px; }
.form-actions { display: flex; flex-wrap: wrap; gap: 10px; }
@media (max-width: 520px) { .coordinate-fields { grid-template-columns: 1fr; } }
</style>

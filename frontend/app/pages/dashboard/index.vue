<script setup lang="ts">
import type { Job } from "~/types/job"

definePageMeta({ middleware: "auth" })
useHead({ title: "Dashboard" })

const authStore = useAuthStore()
const userStore = useUserStore()
const jobsStore = useJobsStore()
const providersStore = useProvidersStore()
const loading = ref(true)
const pageError = ref("")

const user = computed(() => userStore.user || authStore.user)
const activeJobs = computed(() => jobsStore.jobs.filter(job => !["completed", "cancelled"].includes(job.status)))
const quotedJobs = computed(() => jobsStore.jobs.filter(job => job.status === "quoted"))
const completedJobs = computed(() => jobsStore.jobs.filter(job => job.status === "completed"))
const recentJobs = computed(() => [...jobsStore.jobs].slice(0, 3))

const roleLabel = computed(() => {
  if (user.value?.role === "provider") return "Service provider"
  if (user.value?.role === "admin") return "Administrator"
  return "Customer"
})

const statusLabel = (status: Job["status"]) =>
  status.replaceAll("_", " ")

onMounted(async () => {
  loading.value = true
  pageError.value = ""
  try {
    const currentUser = user.value || await authStore.loadCurrentUser()
    if (!currentUser) {
      await navigateTo("/auth/login")
      return
    }
    await userStore.fetchMyProfile()
    if (currentUser.role === "provider") {
      await Promise.all([
        jobsStore.fetchMyJobs(),
        jobsStore.fetchAvailableJobs(),
        providersStore.fetchMyProfile(),
      ])
    } else if (currentUser.role === "customer") {
      await jobsStore.fetchMyJobs()
    }
  } catch (error: unknown) {
    const detail = (error as { data?: { detail?: string } })?.data?.detail
    pageError.value = detail || jobsStore.error || providersStore.error || userStore.error || "Some dashboard information could not be loaded. Please refresh to try again."
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <main class="dashboard">
    <section class="welcome-panel">
      <div class="welcome-copy">
        <p class="eyebrow">{{ roleLabel }} dashboard</p>
        <h1>Welcome back<span v-if="user">, {{ user.full_name.split(" ")[0] }}</span>.</h1>
        <p class="welcome-description">
          <template v-if="user?.role === 'provider'">Your work, new opportunities, and professional profile are all in one place.</template>
          <template v-else-if="user?.role === 'admin'">Manage marketplace jobs, services, and provider profiles.</template>
          <template v-else>Keep your home-service requests moving and find help for your next project.</template>
        </p>
        <div class="welcome-actions">
          <NuxtLink v-if="user?.role === 'customer'" to="/jobs/create" class="btn btn-accent">Request a service <span aria-hidden="true">→</span></NuxtLink>
          <NuxtLink v-else-if="user?.role === 'provider'" to="/jobs" class="btn btn-accent">Explore available jobs <span aria-hidden="true">→</span></NuxtLink>
          <NuxtLink v-else to="/jobs" class="btn btn-accent">Manage jobs <span aria-hidden="true">→</span></NuxtLink>
          <NuxtLink to="/profiles" class="welcome-link">Account details <span aria-hidden="true">↗</span></NuxtLink>
        </div>
      </div>
      <img
        src="https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?auto=format&fit=crop&w=1200&q=85"
        alt="A bright, welcoming home"
      />
    </section>

    <AppLoader v-if="loading" />
    <template v-else>
      <AppAlert v-if="pageError" type="error">{{ pageError }}</AppAlert>

      <section v-if="user?.role === 'customer'" class="overview">
        <div class="section-heading">
          <div><p class="eyebrow section-eyebrow">Your activity</p><h2>Service request overview</h2></div>
          <NuxtLink to="/jobs" class="text-link">View all jobs <span aria-hidden="true">→</span></NuxtLink>
        </div>
        <div class="stats-grid">
          <article class="stat-card"><span class="stat-icon blue">⌂</span><div><strong>{{ jobsStore.jobs.length }}</strong><span>Total requests</span></div></article>
          <article class="stat-card"><span class="stat-icon orange">↻</span><div><strong>{{ activeJobs.length }}</strong><span>Active requests</span></div></article>
          <article class="stat-card"><span class="stat-icon purple">＄</span><div><strong>{{ quotedJobs.length }}</strong><span>Quotes to review</span></div></article>
          <article class="stat-card"><span class="stat-icon green">✓</span><div><strong>{{ completedJobs.length }}</strong><span>Completed</span></div></article>
        </div>
      </section>

      <section v-else-if="user?.role === 'provider'" class="overview">
        <div class="section-heading">
          <div><p class="eyebrow section-eyebrow">Your business</p><h2>Provider overview</h2></div>
          <NuxtLink to="/providers" class="text-link">Manage profile <span aria-hidden="true">→</span></NuxtLink>
        </div>
        <div class="stats-grid">
          <article class="stat-card"><span class="stat-icon blue">⌕</span><div><strong>{{ jobsStore.availableJobs.length }}</strong><span>Matching opportunities</span></div></article>
          <article class="stat-card"><span class="stat-icon orange">↻</span><div><strong>{{ activeJobs.length }}</strong><span>Active jobs</span></div></article>
          <article class="stat-card"><span class="stat-icon purple">★</span><div><strong>{{ providersStore.provider?.rating_avg.toFixed(1) ?? "—" }}</strong><span>{{ providersStore.provider?.rating_count ?? 0 }} customer reviews</span></div></article>
          <article class="stat-card"><span class="stat-icon green">✓</span><div><strong>{{ providersStore.provider?.completed_job_count ?? 0 }} / 5</strong><span>Jobs to verified badge</span></div></article>
        </div>
        <AppAlert v-if="providersStore.provider && !providersStore.provider.is_verified" type="info">
          Submit your ID images and live selfie before quoting. A matching skill and availability are also required. The marketplace badge is earned after 5 completed jobs; ID images are not automatically authenticated.
        </AppAlert>
      </section>

      <section v-else-if="user?.role === 'admin'" class="overview">
        <div class="section-heading">
          <div><p class="eyebrow section-eyebrow">Marketplace tools</p><h2>Administration</h2></div>
          <NuxtLink to="/admin/services" class="text-link">Manage services <span aria-hidden="true">→</span></NuxtLink>
        </div>
        <div class="admin-callout">
          <span class="stat-icon purple">⌂</span>
          <div><h3>Marketplace jobs and services</h3><p>Update job details, curate service rates and descriptions, and manage provider marketplace badges.</p></div>
          <nav class="admin-actions">
            <NuxtLink to="/jobs" class="btn btn-primary">Manage jobs</NuxtLink>
            <NuxtLink to="/admin/services" class="btn btn-outline">Manage services</NuxtLink>
            <NuxtLink to="/admin/providers" class="btn btn-outline">Provider badges</NuxtLink>
          </nav>
        </div>
      </section>

      <section v-if="user?.role === 'customer' || user?.role === 'provider'" class="activity-section">
        <div class="section-heading">
          <div><p class="eyebrow section-eyebrow">Latest updates</p><h2>{{ user?.role === "provider" ? "Your recent jobs" : "Recent service requests" }}</h2></div>
          <NuxtLink to="/jobs" class="text-link">See all activity <span aria-hidden="true">→</span></NuxtLink>
        </div>
        <div v-if="recentJobs.length" class="recent-jobs">
          <NuxtLink v-for="job in recentJobs" :key="job.id" :to="`/jobs/${job.id}`" class="recent-job">
            <span class="job-mark" aria-hidden="true">⌂</span>
            <span class="job-info"><strong>Job #{{ job.id }}</strong><span>{{ job.description }}</span></span>
            <span class="job-status" :class="`status-${job.status}`">{{ statusLabel(job.status) }}</span>
            <span class="job-arrow" aria-hidden="true">→</span>
          </NuxtLink>
        </div>
        <div v-else class="empty-activity">
          <div><h3>No requests yet</h3><p>{{ user?.role === "provider" ? "Matching jobs will appear here when they are available." : "Start by choosing a service and telling us what you need." }}</p></div>
          <NuxtLink v-if="user?.role === 'customer'" to="/categories" class="btn btn-outline">Browse services</NuxtLink>
          <NuxtLink v-else to="/jobs" class="btn btn-outline">Browse jobs</NuxtLink>
        </div>
      </section>

      <section class="dashboard-links">
        <div class="section-heading">
          <div><p class="eyebrow section-eyebrow">Quick access</p><h2>Where would you like to go?</h2></div>
        </div>
        <nav class="links-grid">
          <NuxtLink v-if="user?.role === 'customer'" to="/jobs/create" class="dashboard-card"><span class="link-icon">＋</span><span><strong>Post a job</strong><small>Tell providers what you need.</small></span><span class="link-arrow">→</span></NuxtLink>
          <NuxtLink to="/jobs" class="dashboard-card"><span class="link-icon">▤</span><span><strong>{{ user?.role === "provider" ? "Jobs and opportunities" : "My jobs" }}</strong><small>Track requests and job progress.</small></span><span class="link-arrow">→</span></NuxtLink>
          <NuxtLink v-if="user?.role === 'provider'" to="/providers" class="dashboard-card"><span class="link-icon">⚙</span><span><strong>Provider profile</strong><small>Update skills, location, and availability.</small></span><span class="link-arrow">→</span></NuxtLink>
          <NuxtLink v-if="user?.role === 'customer'" to="/categories" class="dashboard-card"><span class="link-icon">⌂</span><span><strong>Browse services</strong><small>Explore all available service types.</small></span><span class="link-arrow">→</span></NuxtLink>
          <NuxtLink v-if="user?.role === 'customer'" to="/quotes" class="dashboard-card"><span class="link-icon">＄</span><span><strong>Review quotes</strong><small>Compare responses for a job.</small></span><span class="link-arrow">→</span></NuxtLink>
          <NuxtLink to="/profiles" class="dashboard-card"><span class="link-icon">◎</span><span><strong>Account profile</strong><small>Check your personal information.</small></span><span class="link-arrow">→</span></NuxtLink>
          <NuxtLink to="/reviews" class="dashboard-card"><span class="link-icon">★</span><span><strong>Provider reviews</strong><small>Explore feedback for providers.</small></span><span class="link-arrow">→</span></NuxtLink>
          <NuxtLink v-if="user?.role === 'admin'" to="/admin/services" class="dashboard-card"><span class="link-icon">⌂</span><span><strong>Manage services</strong><small>Add, edit, and remove marketplace services.</small></span><span class="link-arrow">→</span></NuxtLink>
          <NuxtLink v-if="user?.role === 'admin'" to="/admin/providers" class="dashboard-card"><span class="link-icon">✓</span><span><strong>Provider marketplace badges</strong><small>Review document-submission status and manage badges.</small></span><span class="link-arrow">→</span></NuxtLink>
        </nav>
      </section>
    </template>
  </main>
</template>

<style scoped>
.dashboard { width: min(1200px, 100% - 32px); margin: 0 auto; padding: 30px 0 54px; }
.welcome-panel { display: grid; grid-template-columns: 1fr .9fr; align-items: center; gap: 36px; overflow: hidden; margin-bottom: 38px; padding: clamp(24px, 4vw, 44px); color: #fff; background: var(--color-dark); border-radius: 20px; }
.welcome-copy { max-width: 590px; }
.eyebrow { margin: 0 0 10px; color: #ffc48d; font-size: 12px; font-weight: 700; letter-spacing: .15em; text-transform: uppercase; }
h1 { margin: 0 0 14px; color: #fff; font-size: clamp(34px, 5vw, 54px); line-height: 1.08; letter-spacing: -.035em; }
.welcome-description { max-width: 520px; margin: 0; color: #dbe5f2; font-size: 16px; line-height: 1.7; }
.welcome-actions { display: flex; flex-wrap: wrap; align-items: center; gap: 20px; margin-top: 24px; }
.welcome-link { color: #fff; font-size: 14px; font-weight: 600; text-decoration: none; }
.welcome-link span { margin-left: 5px; color: #ffc48d; }
.welcome-panel img { width: 100%; height: 250px; object-fit: cover; border-radius: 14px; }
.overview, .activity-section, .dashboard-links { margin-top: 34px; }
.section-heading { display: flex; justify-content: space-between; align-items: end; gap: 20px; margin-bottom: 18px; }
.section-eyebrow { margin-bottom: 5px; color: var(--color-primary); }
h2 { margin: 0; font-size: clamp(23px, 3vw, 30px); letter-spacing: -.025em; }
.text-link { flex: 0 0 auto; color: var(--color-primary); font-size: 14px; font-weight: 700; text-decoration: none; }
.text-link span { margin-left: 5px; }
.stats-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; margin-bottom: 16px; }
.stat-card { display: flex; align-items: center; gap: 14px; min-height: 105px; padding: 18px; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-lg); }
.stat-icon { display: grid; place-items: center; flex: 0 0 44px; width: 44px; height: 44px; border-radius: 13px; font-size: 20px; font-weight: 700; }
.stat-icon.blue { color: #1d4ed8; background: #dbeafe; }
.stat-icon.orange { color: #c2410c; background: #ffedd5; }
.stat-icon.purple { color: #6d28d9; background: #ede9fe; }
.stat-icon.green { color: #15803d; background: #dcfce7; }
.stat-card strong, .stat-card div span { display: block; }
.stat-card strong { font-size: 23px; line-height: 1.25; text-transform: capitalize; }
.stat-card div span { margin-top: 3px; color: var(--color-muted); font-size: 13px; }
.recent-jobs { overflow: hidden; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-lg); }
.recent-job { display: flex; align-items: center; gap: 14px; padding: 16px 18px; color: inherit; text-decoration: none; }
.recent-job + .recent-job { border-top: 1px solid var(--color-border); }
.recent-job:hover { background: var(--color-page); }
.job-mark { display: grid; place-items: center; flex: 0 0 40px; width: 40px; height: 40px; color: var(--color-primary); background: var(--color-primary-soft); border-radius: 12px; font-size: 20px; }
.job-info { display: grid; flex: 1; min-width: 0; gap: 2px; }
.job-info strong { font-size: 14px; }
.job-info span { overflow: hidden; color: var(--color-muted); font-size: 13px; text-overflow: ellipsis; white-space: nowrap; }
.job-status { padding: 5px 10px; color: #334155; background: #e2e8f0; border-radius: 999px; font-size: 12px; font-weight: 700; text-transform: capitalize; white-space: nowrap; }
.status-quoted { color: #92400e; background: #fef3c7; }
.status-accepted, .status-en_route, .status-in_progress { color: #5b21b6; background: #ede9fe; }
.status-completed { color: #166534; background: #dcfce7; }
.status-cancelled { color: #991b1b; background: #fee2e2; }
.job-arrow { color: var(--color-primary); font-size: 18px; }
.empty-activity, .admin-callout { display: flex; justify-content: space-between; align-items: center; gap: 20px; padding: 24px; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-lg); }
.empty-activity h3, .admin-callout h3 { margin: 0 0 5px; }
.empty-activity p, .admin-callout p { margin: 0; color: var(--color-muted); }
.admin-callout > div { flex: 1; }
.admin-actions { display: flex; flex-wrap: wrap; gap: 8px; }
.links-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
.dashboard-card { display: flex; align-items: center; gap: 14px; padding: 17px; color: inherit; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-lg); text-decoration: none; transition: transform .15s ease, box-shadow .15s ease; }
.dashboard-card:hover { transform: translateY(-2px); box-shadow: var(--shadow-md); }
.link-icon { display: grid; place-items: center; flex: 0 0 42px; width: 42px; height: 42px; color: var(--color-primary); background: var(--color-primary-soft); border-radius: 12px; font-size: 20px; }
.dashboard-card > span:nth-child(2) { display: grid; flex: 1; gap: 3px; }
.dashboard-card strong { font-size: 14px; }
.dashboard-card small { color: var(--color-muted); font-size: 12px; }
.link-arrow { color: var(--color-primary); font-size: 18px; }
@media (max-width: 800px) { .welcome-panel { grid-template-columns: 1fr; } .welcome-panel img { height: 210px; } .stats-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 560px) { .dashboard { padding-top: 18px; } .section-heading { align-items: flex-start; flex-direction: column; } .stats-grid, .links-grid { grid-template-columns: 1fr; } .recent-job { gap: 10px; padding: 13px; } .job-status { font-size: 11px; } .empty-activity, .admin-callout { align-items: flex-start; flex-direction: column; } }
</style>

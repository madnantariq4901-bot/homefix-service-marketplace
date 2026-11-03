<script setup lang="ts">
definePageMeta({ middleware: "auth" })
useHead({ title: "Review quotes" })

const route = useRoute()
const quotesStore = useQuotesStore()
const jobsStore = useJobsStore()
const authStore = useAuthStore()
const jobId = ref<number | null>(null)
const message = ref("")
const loadingJobs = ref(true)

const quoteStatuses = ["quoted", "accepted", "en_route", "in_progress", "completed"]
const jobsWithQuotes = computed(() => jobsStore.jobs.filter(job => quoteStatuses.includes(job.status)))

async function loadQuotes() {
  message.value = ""
  if (!jobId.value) return
  try {
    await jobsStore.fetchJob(jobId.value)
    await quotesStore.fetchJobQuotes(jobId.value)
  } catch (err: any) {
    message.value = err?.data?.detail || quotesStore.error || "Unable to load quotes."
  }
}

watch(jobId, (id) => {
  if (id) loadQuotes()
})

async function acceptQuote(quoteId: number) {
  if (!jobId.value) return
  message.value = ""
  try {
    const job = await quotesStore.acceptQuote(jobId.value, quoteId)
    await navigateTo(`/jobs/${job.id}`)
  } catch (err: any) {
    message.value = err?.data?.detail || quotesStore.error || "Unable to accept quote."
  }
}

onMounted(async () => {
  try {
    if (!authStore.user) await authStore.loadCurrentUser()
    await jobsStore.fetchMyJobs()
    const fromQuery = Number(route.query.job)
    const preferred =
      jobsWithQuotes.value.find(job => job.id === fromQuery) ??
      jobsWithQuotes.value.find(job => job.status === "quoted") ??
      jobsWithQuotes.value[0]
    if (preferred) jobId.value = preferred.id
  } catch (err: any) {
    message.value = err?.data?.detail || jobsStore.error || "Unable to load your jobs."
  } finally {
    loadingJobs.value = false
  }
})
</script>

<template>
  <main class="quotes-page">
    <section class="quotes-hero">
      <div>
        <p class="eyebrow">Compare before you choose</p>
        <h1>{{ authStore.user?.role === 'provider' ? 'Review your submitted quotes.' : authStore.user?.role === 'admin' ? 'Review marketplace quotes.' : 'Review job quotes.' }}</h1>
        <p>{{ authStore.user?.role === 'provider' ? 'See only the quotes you submitted and the status of those jobs.' : authStore.user?.role === 'admin' ? 'Review quotes across marketplace jobs for administrative purposes.' : 'Pick one of your jobs to compare provider responses and decide which quote works best for you.' }}</p>
        <NuxtLink to="/jobs" class="hero-link">Go to your jobs <span aria-hidden="true">→</span></NuxtLink>
      </div>
      <img
        src="https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?auto=format&fit=crop&w=1100&q=85"
        alt="Planning and comparing project estimates"
      />
    </section>
    <section class="quote-content">
      <div class="intro">
        <p class="eyebrow section-eyebrow">Your next decision</p>
        <h2>{{ authStore.user?.role === 'provider' ? 'Your submitted quotes' : authStore.user?.role === 'admin' ? 'Quotes by job' : 'Find the right fit for your job.' }}</h2>
        <p>{{ authStore.user?.role === 'provider' ? 'Only your own submitted quote is shown for each job.' : authStore.user?.role === 'admin' ? 'Select a job to review its quotes.' : 'Only jobs that have received quotes are listed here. Quotes are tied to a specific request.' }}</p>
      </div>
      <form class="search-box" @submit.prevent="loadQuotes">
        <label for="job-select">Choose a job</label>
        <div class="search-fields">
          <select id="job-select" v-model.number="jobId" :disabled="!jobsWithQuotes.length">
            <option v-for="job in jobsWithQuotes" :key="job.id" :value="job.id">
              Job #{{ job.id }} · {{ job.description.slice(0, 40) }} ({{ job.status.replaceAll("_", " ") }})
            </option>
          </select>
          <button type="submit" :disabled="!jobId || quotesStore.loading">{{ quotesStore.loading ? "Loading…" : "Refresh quotes" }}</button>
        </div>
      </form>
    </section>
    <AppAlert v-if="message" type="error">{{ message }}</AppAlert>
    <AppLoader v-if="loadingJobs || quotesStore.loading" />
    <div v-else-if="!jobsWithQuotes.length" class="empty-quotes">
      <span aria-hidden="true">＄</span>
      <div><h3>No quotes yet</h3><p>None of your jobs have received a quote. Check back soon, or <NuxtLink to="/jobs">view your jobs</NuxtLink>.</p></div>
    </div>
    <div v-else-if="!quotesStore.quotes.length" class="empty-quotes">
      <span aria-hidden="true">＄</span>
      <div><h3>No quotes for this job</h3><p>Providers have not sent a quote for this job yet.</p></div>
    </div>
    <div v-else>
      <QuoteCard
        v-for="quote in quotesStore.quotes"
        :key="quote.id"
        :quote="quote"
        :can-accept="(authStore.user?.role === 'customer' || (authStore.user?.role === 'admin' && jobsStore.currentJob?.customer_id === authStore.user?.id)) && jobsStore.currentJob?.status === 'quoted'"
        :loading="quotesStore.loading"
        @accept="acceptQuote"
      />
    </div>
  </main>
</template>

<style scoped>
.quotes-page { max-width: 1200px; margin: 0 auto; padding: 28px; }
.quotes-hero { display: grid; grid-template-columns: 1fr .85fr; align-items: center; gap: 34px; overflow: hidden; margin-bottom: 36px; padding: clamp(24px, 4vw, 40px); color: #fff; background: var(--color-dark); border-radius: 18px; }
.quotes-hero h1 { margin: 0 0 12px; color: #fff; font-size: clamp(36px, 4vw, 50px); line-height: 1.08; }
.quotes-hero p:not(.eyebrow) { max-width: 500px; color: #dbe5f2; }
.quotes-hero img { width: 100%; height: 220px; object-fit: cover; border-radius: 14px; }
.eyebrow { margin: 0 0 9px; color: #ffc48d; font-size: 12px; font-weight: 700; letter-spacing: .15em; text-transform: uppercase; }
.hero-link { color: #fff; font-weight: 700; text-decoration: none; }
.hero-link span { margin-left: 6px; color: #ffc48d; }
.quote-content { display: grid; grid-template-columns: 1fr 1fr; align-items: center; gap: 32px; margin: 0 0 28px; padding: 24px; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-lg); }
.section-eyebrow { color: var(--color-primary); }
.intro h2 { margin: 0 0 7px; font-size: 24px; }
.intro > p:last-child { margin: 0; color: var(--color-muted); }
.search-box { margin: 0; }
.search-box label { display: block; margin-bottom: 7px; font-size: 14px; font-weight: 700; }
.search-fields { display: flex; gap: 10px; }
.search-fields button { flex: 0 0 auto; }
.empty-quotes { display: flex; align-items: center; gap: 16px; padding: 22px; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-lg); }
.empty-quotes > span { display: grid; place-items: center; flex: 0 0 48px; width: 48px; height: 48px; color: #6d28d9; background: #ede9fe; border-radius: 14px; font-size: 23px; }
.empty-quotes h3 { margin: 0 0 4px; }
.empty-quotes p { margin: 0; color: var(--color-muted); }
@media (max-width: 760px) { .quotes-page { padding: 18px; } .quotes-hero { grid-template-columns: 1fr; } .quotes-hero img { height: 200px; } .quote-content { grid-template-columns: 1fr; } }
@media (max-width: 520px) { .search-fields { flex-direction: column; } }
.search-fields select { flex: 1; min-width: 0; }
</style>

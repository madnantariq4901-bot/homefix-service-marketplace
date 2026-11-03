<script setup lang="ts">
import type { JobStatus } from "~/types/job"
import { getCategoryMeta } from "~/utils/categoryMeta"

definePageMeta({ middleware: "auth" })

const route = useRoute()
const authStore = useAuthStore()
const jobsStore = useJobsStore()
const quotesStore = useQuotesStore()
const providersStore = useProvidersStore()
const categoriesStore = useCategoriesStore()
const jobId = Number(route.params.id)
const quoteAmount = ref("")
const finalAmount = ref("")
const rating = ref(4)
const reviewComment = ref("")
const showReviewModal = ref(false)
const reviewModalState = ref<"form" | "success">("form")
const reviewSubmitted = ref(false)
const reviewError = ref("")
const reviewKey = `homefix-review-submitted-${jobId}`
const actionError = ref("")
const actionMessage = ref("")
const job = computed(() => jobsStore.currentJob)
const user = computed(() => authStore.user)
const categoryLabel = computed(() => {
  const category = categoriesStore.categories.find(item => item.id === job.value?.category_id)
  return category ? getCategoryMeta(category.name).label : `Category #${job.value?.category_id ?? ""}`
})
const isCustomer = computed(() => Boolean(job.value && user.value?.id === job.value.customer_id))
const isAssignedProvider = computed(() => Boolean(job.value && providersStore.provider && job.value.provider_id === providersStore.provider.id))
const needsProviderSkill = computed(() => Boolean(
  job.value && user.value?.role === "provider" && job.value.provider_id === null &&
  ["requested", "quoted"].includes(job.value.status) &&
  !providersStore.provider?.skills.some(skill => skill.category_id === job.value?.category_id)
))
const canChat = computed(() => Boolean(job.value?.provider_id !== null && (isCustomer.value || isAssignedProvider.value)))
const chatPartnerName = computed(() => isCustomer.value
  ? job.value?.provider_name || "Service provider"
  : job.value?.customer_name || "Customer")
const canConfirmCompletion = computed(() => Boolean(
  isCustomer.value && job.value?.status === "in_progress" && job.value.completion_requested
))
const isAwaitingCustomerConfirmation = computed(() => Boolean(
  isAssignedProvider.value && job.value?.status === "in_progress" && job.value.completion_requested
))
const canQuote = computed(() => Boolean(
  job.value && user.value?.role === "provider" && providersStore.provider?.is_available &&
  (job.value.provider_id === null || isAssignedProvider.value) &&
  ["requested", "quoted"].includes(job.value.status) &&
  providersStore.provider?.skills.some(skill => skill.category_id === job.value?.category_id)
))
const nextStatus = computed<JobStatus | null>(() => {
  if (!job.value || !isAssignedProvider.value) return null
  if (job.value.status === "accepted") return "en_route"
  if (job.value.status === "en_route") return "in_progress"
  if (job.value.status === "in_progress") return "completed"
  return null
})
const canCancel = computed(() => Boolean(
  job.value && ((isCustomer.value && ["requested", "quoted"].includes(job.value.status)) ||
  (isAssignedProvider.value && ["requested", "quoted", "accepted"].includes(job.value.status)))
))

onMounted(async () => {
  try {
    await categoriesStore.fetchCategories()
    if (!authStore.user) await authStore.loadCurrentUser()
    await jobsStore.fetchJob(jobId)
    try {
      // Server is authoritative; fall back to localStorage if the job hasn't loaded yet.
      reviewSubmitted.value = job.value?.has_review ?? (localStorage.getItem(reviewKey) === "submitted")
    } catch {
      reviewSubmitted.value = job.value?.has_review ?? false
    }
    if (authStore.user?.role === "provider") await providersStore.fetchMyProfile().catch(() => undefined)
    if (job.value && ["quoted", "accepted", "en_route", "in_progress", "completed"].includes(job.value.status)) {
      await quotesStore.fetchJobQuotes(jobId).catch(() => undefined)
    }
  } catch (err: any) {
    actionError.value = err?.data?.detail || jobsStore.error || "Unable to load this job."
  }
})

async function submitQuote() {
  actionError.value = ""
  actionMessage.value = ""
  const amount = Number(quoteAmount.value)
  if (!Number.isFinite(amount) || amount <= 0) {
    actionError.value = "Enter a quote amount greater than zero."
    return
  }
  try {
    await jobsStore.submitQuote(jobId, amount)
    await quotesStore.fetchJobQuotes(jobId)
    actionMessage.value = "Quote submitted."
  } catch (err: any) {
    actionError.value = err?.data?.detail || jobsStore.error || "Unable to submit quote."
  }
}

async function acceptQuote(quoteId: number) {
  actionError.value = ""
  actionMessage.value = ""
  try {
    jobsStore.currentJob = await quotesStore.acceptQuote(jobId, quoteId)
    actionMessage.value = "Quote accepted."
  } catch (err: any) {
    actionError.value = err?.data?.detail || quotesStore.error || "Unable to accept quote."
  }
}

async function changeStatus(status: JobStatus) {
  actionError.value = ""
  actionMessage.value = ""
  try {
    const providerRequestsCompletion = status === "completed" && user.value?.role === "provider"
    const data = providerRequestsCompletion
      ? { status, final_amount: Number(finalAmount.value) }
      : { status }
    if (providerRequestsCompletion && (!Number.isFinite(Number(finalAmount.value)) || Number(finalAmount.value) <= 0)) {
      actionError.value = "Enter a final amount greater than zero."
      return
    }
    await jobsStore.updateStatus(jobId, data)
    // Show the popup only after the customer confirms completion.
    if (status === "completed" && isCustomer.value && !reviewSubmitted.value) {
      openReviewModal()
    }
    actionMessage.value = providerRequestsCompletion
      ? "Completion requested. The customer must confirm before this job is counted as complete."
      : status === "completed"
        ? "Completion confirmed."
        : status === "en_route"
          ? "The customer has been notified that you are on the way."
          : `Job status updated to ${status.replaceAll("_", " ")}.`
    if (["quoted", "accepted", "completed"].includes(status)) await quotesStore.fetchJobQuotes(jobId).catch(() => undefined)
  } catch (err: any) {
    actionError.value = err?.data?.detail || jobsStore.error || "Unable to update job status."
  }
}

function openReviewModal() {
  if (reviewSubmitted.value) return
  reviewError.value = ""
  reviewModalState.value = "form"
  showReviewModal.value = true
}

function closeReviewModal() {
  showReviewModal.value = false
}

async function submitReview() {
  reviewError.value = ""
  try {
    await jobsStore.createReview(jobId, {
      rating: rating.value,
      ...(reviewComment.value.trim()
        ? { comment: reviewComment.value.trim() }
        : {}),
    })

    reviewSubmitted.value = true
    try {
      localStorage.setItem(reviewKey, "submitted")
    } catch {
      // The saved review on the server is authoritative.
    }

    reviewModalState.value = "success"
    window.setTimeout(() => {
      showReviewModal.value = false
    }, 2200)
  } catch (err: any) {
    reviewError.value =
      err?.data?.detail ||
      jobsStore.error ||
      "Unable to submit your review. Please try again."
  }
}
</script>

<template>
  <main class="job-page">
    <AppLoader v-if="jobsStore.loading && !job" />
    <AppAlert v-else-if="!job" type="error">{{ actionError || jobsStore.error || "Job not found." }}</AppAlert>
    <div v-else class="job-layout">
      <section class="job-panel">
        <header>
        <div>
          <p class="eyebrow">Job #{{ job.id }}</p>
          <h1>{{ job.description }}</h1>
        </div>
        <span class="status">{{ isAwaitingCustomerConfirmation ? "awaiting customer confirmation" : job.status.replaceAll("_", " ") }}</span>
      </header>
      <JobTimeline :status="job.status" />
      <dl>
        <div><dt>Address</dt><dd>{{ job.address }}</dd></div>
        <div v-if="job.lat != null && job.lng != null">
          <dt>Exact map location</dt>
          <dd>
            <a :href="`https://www.google.com/maps/search/?api=1&query=${job.lat},${job.lng}`" target="_blank" rel="noopener">
              Open service pin in Google Maps
            </a>
          </dd>
        </div>
        <div><dt>Service</dt><dd>{{ categoryLabel }}</dd></div>
        <div><dt>Quote amount</dt><dd>{{ job.quoted_amount ?? "No quote yet" }}</dd></div>
        <div><dt>Final amount</dt><dd>{{ job.final_amount ?? "Not completed" }}</dd></div>
        <div><dt>Posted by</dt><dd>{{ job.customer_name ?? `Customer #${job.customer_id}` }}</dd></div>
        <div v-if="job.customer_email"><dt>Customer email</dt><dd><a :href="`mailto:${job.customer_email}`">{{ job.customer_email }}</a></dd></div>
        <div><dt>Service provider</dt><dd>{{ job.provider_name ?? "Waiting for a provider" }}</dd></div>
        <div v-if="job.provider_email"><dt>Provider email</dt><dd><a :href="`mailto:${job.provider_email}`">{{ job.provider_email }}</a></dd></div>
      </dl>
      <JobAttachments v-if="job.attachments?.length" :job-id="jobId" :attachments="job.attachments" />

      <AppAlert v-if="actionError || jobsStore.error || quotesStore.error" type="error">{{ actionError || jobsStore.error || quotesStore.error }}</AppAlert>
      <AppAlert v-if="actionMessage" type="success">{{ actionMessage }}</AppAlert>

      <section v-if="needsProviderSkill" class="action-section">
        <h2>This service isn’t on your profile yet</h2>
        <p>You can review this invitation, but you need to add the matching service skill and meet availability and identity requirements before submitting a quote.</p>
        <NuxtLink class="btn btn-outline" to="/providers">Update provider profile</NuxtLink>
      </section>

      <section v-if="canQuote && !providersStore.provider?.identity_documents_submitted" class="action-section">
        <h2>Submit identity documents before quoting</h2>
        <p>Submit both sides of your government ID and capture a live selfie to continue.</p>
        <ProviderIdentityForm />
      </section>

      <section v-else-if="canQuote" class="action-section">
        <h2>Submit a quote</h2>
        <form @submit.prevent="submitQuote">
          <label>Amount <input v-model="quoteAmount" type="number" min="0.01" step="0.01" required /></label>
          <button type="submit" :disabled="jobsStore.loading">{{ jobsStore.loading ? "Submitting..." : "Submit quote" }}</button>
        </form>
      </section>

      <section v-if="quotesStore.quotes.length" class="action-section">
        <h2>Quotes</h2>
        <QuoteCard
          v-for="quote in quotesStore.quotes"
          :key="quote.id"
          :quote="quote"
          :can-accept="isCustomer && job.status === 'quoted'"
          :loading="quotesStore.loading"
          @accept="acceptQuote"
        />
      </section>

      <section v-if="nextStatus || canConfirmCompletion" class="action-section">
        <h2>Update job</h2>
        <p v-if="isAwaitingCustomerConfirmation">Completion requested. The job will count toward your provider badge after the customer confirms.</p>
        <form v-else-if="nextStatus === 'completed' && isAssignedProvider" @submit.prevent="changeStatus('completed')">
          <label>Final amount <input v-model="finalAmount" type="number" min="0.01" step="0.01" required /></label>
          <button type="submit" :disabled="jobsStore.loading">Request completion</button>
        </form>
        <button v-else-if="canConfirmCompletion" type="button" :disabled="jobsStore.loading" @click="changeStatus('completed')">
          Confirm job completion
        </button>
        <button v-else-if="nextStatus" type="button" :disabled="jobsStore.loading" @click="changeStatus(nextStatus)">
          {{ nextStatus === 'en_route' ? "On the way" : "Start work" }}
        </button>
      </section>

      <section v-if="canCancel" class="action-section">
        <button class="cancel-button" type="button" :disabled="jobsStore.loading" @click="changeStatus('cancelled')">Cancel job</button>
      </section>

      <section v-if="isCustomer && job.status === 'completed' && !reviewSubmitted" class="action-section">
        <h2>Review this service</h2>
        <p>You can rate the service with 1–5 stars. A written comment is optional.</p>
        <button type="button" @click="openReviewModal">Rate this service</button>
      </section>
      <section v-else-if="isCustomer && job.status === 'completed' && reviewSubmitted" class="action-section">
        <h2>Review submitted</h2>
        <p>Thank you for sharing your experience.</p>
      </section>
        <NuxtLink class="back-link" to="/jobs">Back to jobs</NuxtLink>
      </section>
      <JobChat v-if="canChat" :job-id="jobId" :partner-name="chatPartnerName" />
    </div>
  </main>

  <Teleport to="body">
    <div
      v-if="showReviewModal"
      class="review-modal-backdrop"
      role="presentation"
      @click.self="closeReviewModal"
      @keydown.esc="closeReviewModal"
    >
      <section class="review-modal" role="dialog" aria-modal="true" aria-labelledby="review-modal-title">
        <button class="review-modal-close" type="button" aria-label="Close review popup" @click="closeReviewModal">×</button>

        <template v-if="reviewModalState === 'form'">
          <div class="review-modal-symbol" aria-hidden="true">★</div>
          <p class="review-modal-kicker">JOB COMPLETED</p>
          <h2 id="review-modal-title">How was your service?</h2>
          <p class="review-modal-description">Your rating helps other customers choose a trusted provider.</p>

          <form class="review-modal-form" @submit.prevent="submitReview">
            <fieldset class="review-star-fieldset">
              <legend>Your rating</legend>
              <div class="review-stars" role="radiogroup" aria-label="Rating from 1 to 5 stars">
                <button
                  v-for="star in [1, 2, 3, 4, 5]"
                  :key="star"
                  type="button"
                  role="radio"
                  :aria-checked="rating === star"
                  :aria-label="`${star} out of 5 stars`"
                  :class="{ 'star-selected': star <= rating }"
                  @click="rating = star"
                >{{ star <= rating ? "★" : "☆" }}</button>
              </div>
              <p class="review-rating-label">{{ rating === 5 ? "Excellent" : rating === 4 ? "Good" : rating === 3 ? "Average" : rating === 2 ? "Below average" : "Poor" }}</p>
            </fieldset>

            <label class="review-comment-label" for="review-modal-comment">
              Written review <span>(optional)</span>
            </label>
            <textarea
              id="review-modal-comment"
              v-model="reviewComment"
              rows="4"
              maxlength="2000"
              placeholder="Tell us about your experience…"
            />

            <p v-if="reviewError" class="review-modal-error" role="alert">{{ reviewError }}</p>

            <button class="review-submit-button" type="submit" :disabled="jobsStore.loading">
              {{ jobsStore.loading ? "Submitting…" : "Submit review" }}
            </button>
          </form>
          <p class="review-modal-footnote">You can submit a rating without writing a comment.</p>
        </template>

        <template v-else>
          <div class="review-success-symbol" aria-hidden="true">✓</div>
          <h2 id="review-modal-title">Thank you!</h2>
          <p class="review-modal-description">Your rating has been submitted successfully.</p>
        </template>
      </section>
    </div>
  </Teleport>
</template>

<style scoped>
.job-page { padding: 28px 16px; }
.job-layout { display: grid; grid-template-columns: minmax(0, 1fr) 340px; align-items: start; gap: 18px; max-width: 1240px; margin: 0 auto; }
.job-panel { padding: 26px; border: 1px solid var(--color-border); border-radius: 10px; background: var(--color-surface); }
header { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; }
header h1 { margin: 4px 0 18px; font-size: clamp(22px, 3vw, 30px); }
.eyebrow { margin: 0; color: var(--color-muted); }
.status { padding: 5px 9px; border-radius: 5px; background: #edf0f2; text-transform: capitalize; white-space: nowrap; }
dl { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; }
dl div { padding-bottom: 12px; border-bottom: 1px solid var(--color-border); }
dt { color: var(--color-muted); font-size: 13px; }
dd { margin: 4px 0 0; }
.action-section { margin-top: 28px; padding-top: 20px; border-top: 1px solid var(--color-border); }
.action-section h2 { margin-top: 0; font-size: 19px; }
form { display: grid; gap: 14px; max-width: 460px; }
label { display: grid; gap: 7px; font-size: 14px; font-weight: 600; }
textarea { resize: vertical; }
.cancel-button { background: white; color: var(--color-danger); border-color: #d5a3a3; }
.cancel-button:hover:not(:disabled) { background: #fff1f1; }
.back-link { display: inline-block; margin-top: 26px; }
@media (max-width: 850px) { .job-layout { grid-template-columns: minmax(0, 1fr); } }
@media (max-width: 600px) { .job-panel { padding: 18px; } header { flex-direction: column; } dl { grid-template-columns: 1fr; } }


.review-modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 10000;
  display: grid;
  place-items: center;
  padding: 18px;
  background: rgb(8 15 35 / 68%);
  backdrop-filter: blur(7px);
  -webkit-backdrop-filter: blur(7px);
  animation: review-overlay-in 160ms ease-out;
}
.review-modal {
  position: relative;
  width: min(100%, 470px);
  max-height: calc(100dvh - 36px);
  overflow-y: auto;
  padding: 32px 30px 25px;
  color: var(--color-text);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 20px;
  box-shadow: 0 28px 90px rgb(0 0 0 / 30%);
  text-align: center;
  animation: review-card-in 200ms ease-out;
}
.review-modal-close {
  position: absolute;
  top: 11px;
  right: 12px;
  width: 35px;
  height: 35px;
  padding: 0;
  border: 0;
  border-radius: 50%;
  color: var(--color-muted);
  background: transparent;
  font-size: 27px;
  line-height: 1;
}
.review-modal-close:hover { color: var(--color-text); background: var(--color-page); }
.review-modal-symbol, .review-success-symbol {
  display: grid;
  place-items: center;
  width: 58px;
  height: 58px;
  margin: 0 auto 13px;
  border-radius: 50%;
  color: #b77900;
  background: #fff4d6;
  font-size: 29px;
}
.review-modal-kicker { margin: 0 0 6px; color: var(--color-primary); font-size: 11px; font-weight: 800; letter-spacing: .16em; }
.review-modal h2 { margin: 0 20px 8px; font-size: clamp(22px, 4vw, 27px); line-height: 1.25; }
.review-modal-description { margin: 0 auto 20px; max-width: 350px; color: var(--color-muted); font-size: 14px; }
.review-modal-form { display: grid; gap: 13px; max-width: none; text-align: left; }
.review-star-fieldset { min-width: 0; margin: 0; padding: 0; border: 0; text-align: center; }
.review-star-fieldset legend { width: 100%; margin-bottom: 7px; color: var(--color-text); font-size: 14px; font-weight: 700; }
.review-stars { display: flex; justify-content: center; align-items: center; gap: 5px; }
.review-stars button {
  min-width: 43px;
  padding: 1px 2px;
  border: 0;
  color: #cbd5e1;
  background: transparent;
  font-size: 36px;
  line-height: 1.15;
  transition: transform 120ms ease, color 120ms ease;
}
.review-stars button.star-selected { color: #f6b51e; }
.review-stars button:hover { transform: scale(1.12); background: transparent; }
.review-rating-label { margin: 3px 0 0; color: var(--color-muted); font-size: 13px; }
.review-comment-label { display: block; margin-bottom: -7px; font-size: 13px; font-weight: 700; }
.review-comment-label span { color: var(--color-muted); font-weight: 400; }
.review-modal-form textarea { min-height: 95px; resize: vertical; }
.review-modal-error { margin: 0; color: var(--color-danger); font-size: 13px; }
.review-submit-button { width: 100%; min-height: 46px; margin-top: 2px; }
.review-modal-footnote { margin: 13px 0 0; color: var(--color-muted); font-size: 12px; }
.review-success-symbol { color: #167a3e; background: #e8f8ed; font-size: 29px; font-weight: 800; }
.review-modal-backdrop:has(.review-success-symbol) .review-modal { padding-top: 38px; padding-bottom: 32px; }
@keyframes review-overlay-in { from { opacity: 0; } to { opacity: 1; } }
@keyframes review-card-in { from { opacity: 0; transform: translateY(10px) scale(.98); } to { opacity: 1; transform: translateY(0) scale(1); } }
@media (max-width: 480px) {
  .review-modal { padding: 30px 19px 21px; border-radius: 16px; }
  .review-stars { gap: 1px; }
  .review-stars button { min-width: 38px; font-size: 32px; }
}
@media (prefers-reduced-motion: reduce) {
  .review-modal-backdrop, .review-modal { animation: none; }
  .review-stars button { transition: none; }
}
</style>

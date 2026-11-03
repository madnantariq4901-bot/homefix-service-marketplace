<script setup lang="ts">
import { providersService } from "~/services/provider.service"
import type { PublicProvider } from "~/types/provider"

definePageMeta({
})
useHead({ title: "Provider reviews" })

const route = useRoute()
const reviewsStore = useReviewsStore()
const providers = ref<PublicProvider[]>([])
const providerId = ref<number | null>(null)
const hasSearched = ref(false)
const loadingProviders = ref(true)
const providersError = ref("")

async function loadReviews() {
  if (!providerId.value) return
  hasSearched.value = true
  await reviewsStore.fetchProviderReviews(providerId.value)
}

watch(providerId, () => {
  loadReviews()
})

onMounted(async () => {
  try {
    providers.value = await providersService.getPublicProviders({ limit: 100 })
    const fromQuery = Number(route.query.provider)
    if (providers.value.some(provider => provider.id === fromQuery)) providerId.value = fromQuery
  } catch (err: any) {
    providersError.value = err?.data?.detail || "Unable to load providers."
  } finally {
    loadingProviders.value = false
  }
})
</script>

<template>
  <main class="reviews-page">
    <section class="reviews-hero">
      <div>
        <p class="eyebrow">Real feedback, helpful choices</p>
        <h1>Get to know providers through reviews.</h1>
        <p>Read customer feedback shared after completed jobs to learn about a provider’s service experience.</p>
        <NuxtLink to="/providers/browse" class="hero-link">Find a provider <span aria-hidden="true">→</span></NuxtLink>
      </div>
      <img src="https://images.unsplash.com/photo-1521737711867-e3b97375f902?auto=format&fit=crop&w=1100&q=85" alt="People sharing feedback and ideas" />
    </section>

    <section class="review-search">
      <div>
        <p class="eyebrow section-eyebrow">Provider feedback</p>
        <h2>Read reviews by provider</h2>
        <p>Choose a provider to see the customer reviews available for them.</p>
      </div>
      <form class="search-box" @submit.prevent="loadReviews">
        <label for="provider-select">Provider</label>
        <div class="search-fields">
          <select id="provider-select" v-model.number="providerId" :disabled="loadingProviders || !providers.length">
            <option :value="null" disabled>{{ loadingProviders ? "Loading providers…" : "Choose a provider" }}</option>
            <option v-for="provider in providers" :key="provider.id" :value="provider.id">
              {{ provider.full_name }}{{ provider.rating_count ? ` · ★ ${provider.rating_avg.toFixed(1)} (${provider.rating_count})` : "" }}
            </option>
          </select>
          <button type="submit" :disabled="!providerId || reviewsStore.loading">{{ reviewsStore.loading ? "Loading…" : "Load reviews" }}</button>
        </div>
      </form>
    </section>

    <AppAlert v-if="providersError" type="error">{{ providersError }}</AppAlert>
    <AppAlert v-if="reviewsStore.error" type="error">{{ reviewsStore.error }}</AppAlert>
    <AppLoader v-if="reviewsStore.loading" />
    <div v-else-if="hasSearched && !reviewsStore.error && !reviewsStore.reviews.length" class="empty-reviews">
      <span aria-hidden="true">★</span><div><h3>No reviews to show</h3><p>There are no customer reviews available for this provider yet.</p></div>
    </div>
    <section v-else-if="!reviewsStore.error && reviewsStore.reviews.length" class="review-results">
      <div class="results-heading"><h2>Customer reviews</h2><span>{{ reviewsStore.reviews.length }} {{ reviewsStore.reviews.length === 1 ? "review" : "reviews" }}</span></div>
      <ReviewCard
        v-for="review in reviewsStore.reviews"
        :key="review.id"
        :review="review"
      />
    </section>
  </main>
</template>

<style scoped>
.reviews-page { max-width: 1200px; margin: 0 auto; padding: 28px; }
.reviews-hero { display: grid; grid-template-columns: 1fr .85fr; align-items: center; gap: 34px; overflow: hidden; margin-bottom: 34px; padding: clamp(24px, 4vw, 40px); color: #fff; background: var(--color-dark); border-radius: 18px; }
.reviews-hero h1 { max-width: 570px; margin: 0 0 12px; color: #fff; font-size: clamp(34px, 4vw, 48px); line-height: 1.1; }
.reviews-hero p:not(.eyebrow) { max-width: 500px; color: #dbe5f2; }
.reviews-hero img { width: 100%; height: 220px; object-fit: cover; border-radius: 14px; }
.eyebrow { margin: 0 0 9px; color: #ffc48d; font-size: 12px; font-weight: 700; letter-spacing: .15em; text-transform: uppercase; }
.hero-link { color: #fff; font-weight: 700; text-decoration: none; }
.hero-link span { margin-left: 6px; color: #ffc48d; }
.review-search { display: grid; grid-template-columns: 1fr 1fr; align-items: center; gap: 28px; margin-bottom: 26px; padding: 24px; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-lg); }
.section-eyebrow { color: var(--color-primary); }
.review-search h2 { margin: 0 0 6px; font-size: 24px; }
.review-search p:last-child { margin: 0; color: var(--color-muted); }
.search-box label { display: block; margin-bottom: 7px; font-size: 14px; font-weight: 700; }
.search-fields { display: flex; gap: 10px; }
.search-fields button { flex: 0 0 auto; }
.empty-reviews { display: flex; align-items: center; gap: 16px; padding: 22px; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-lg); }
.empty-reviews > span { display: grid; place-items: center; flex: 0 0 48px; width: 48px; height: 48px; color: #b45309; background: #fef3c7; border-radius: 14px; font-size: 23px; }
.empty-reviews h3 { margin: 0 0 4px; }
.empty-reviews p { margin: 0; color: var(--color-muted); }
.review-results { display: grid; gap: 14px; }
.results-heading { display: flex; align-items: center; justify-content: space-between; gap: 16px; margin-bottom: 4px; }
.results-heading h2 { margin: 0; }
.results-heading span { color: var(--color-muted); font-size: 14px; }
@media (max-width: 760px) { .reviews-page { padding: 18px; } .reviews-hero, .review-search { grid-template-columns: 1fr; } .reviews-hero img { height: 200px; } }
@media (max-width: 520px) { .search-fields { flex-direction: column; } }
.search-fields select { flex: 1; min-width: 0; }
</style>

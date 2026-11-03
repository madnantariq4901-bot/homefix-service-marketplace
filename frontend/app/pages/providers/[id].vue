<script setup lang="ts">
import { providersService } from "~/services/provider.service"
import { getCategoryMeta } from "~/utils/categoryMeta"

// Public page: customers can view providers with a marketplace badge before signing in.
const route = useRoute()
const authStore = useAuthStore()
const providerId = Number(route.params.id)
const reviewsStore = useReviewsStore()
const { data: provider, pending, error } = await useAsyncData(
  `public-provider-${providerId}`,
  async () => {
    if (!Number.isInteger(providerId) || providerId < 1) return null
    return await providersService.getPublicProvider(providerId)
  }
)

const initials = computed(() =>
  (provider.value?.full_name ?? "")
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((word) => word[0]!.toUpperCase())
    .join("")
)

useHead(() => ({ title: provider.value?.full_name ?? "Provider profile" }))

onMounted(async () => {
  if (provider.value) {
    await reviewsStore.fetchProviderReviews(providerId)
  }
})
</script>

<template>
  <main class="container provider-page">
    <NuxtLink to="/providers/browse" class="back">← All providers</NuxtLink>

    <AppLoader v-if="pending" />
    <AppAlert v-else-if="error" type="error">Unable to load provider information. Please try again.</AppAlert>
    <AppAlert v-else-if="!provider" type="error">Provider not found.</AppAlert>

    <template v-else>
      <section class="profile">
        <span class="avatar" aria-hidden="true">{{ initials }}</span>
        <div class="info">
          <h1>
            {{ provider.full_name }}
            <span v-if="provider.is_verified" class="verified-badge" aria-label="Marketplace verified badge">✓</span>
          </h1>
          <p class="meta">
            <span v-if="provider.is_verified" class="verified" title="Marketplace badge; not an automatic government ID check">✔ Marketplace badge</span>
            <span :class="provider.is_available ? 'on' : 'off'">{{ provider.is_available ? "Available for jobs" : "Not currently available" }}</span>
          </p>
          <p class="rating">
            <template v-if="provider.rating_count">★ {{ provider.rating_avg.toFixed(1) }} · {{ provider.rating_count }} review{{ provider.rating_count === 1 ? "" : "s" }}</template>
            <template v-else>No reviews yet</template>
            · {{ provider.completed_job_count }} completed job{{ provider.completed_job_count === 1 ? "" : "s" }}
          </p>
        </div>
        <NuxtLink
          v-if="authStore.user?.role !== 'provider'"
          :to="provider.skills.length
            ? `/jobs/create?category=${provider.skills[0]!.category_id}&provider=${provider.id}`
            : '/jobs/create'"
          class="btn btn-accent"
        >Request service from this provider</NuxtLink>
      </section>

      <section class="panel">
        <h2>Services</h2>
        <p v-if="!provider.skills.length" class="muted">No services listed yet.</p>
        <ul v-else class="skills">
          <li v-for="skill in provider.skills" :key="skill.category_id">
            <span class="s-icon" aria-hidden="true">{{ getCategoryMeta(skill.category).icon }}</span>
            <strong>{{ getCategoryMeta(skill.category).label }}</strong>
            <span class="muted">{{ skill.years_experience }} year{{ skill.years_experience === 1 ? "" : "s" }} of experience</span>
          </li>
        </ul>
      </section>

      <section class="panel">
        <h2>Reviews</h2>
        <AppAlert v-if="reviewsStore.error" type="error">{{ reviewsStore.error }}</AppAlert>
        <p v-else-if="!reviewsStore.reviews.length" class="muted">No reviews yet.</p>
        <ReviewCard v-for="review in reviewsStore.reviews" :key="review.id" :review="review" />
      </section>
    </template>
  </main>
</template>

<style scoped>
.provider-page { max-width: 860px; padding: 28px 0 48px; }
.back { display: inline-block; margin-bottom: 16px; text-decoration: none; color: var(--color-primary); font-weight: 600; }
.profile { display: flex; flex-wrap: wrap; align-items: center; gap: 20px; padding: 24px; margin-bottom: 20px; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-lg); }
.avatar { display: grid; place-items: center; flex: none; width: 72px; height: 72px; font-size: 24px; font-weight: 700; color: var(--color-primary); background: var(--color-primary-soft); border-radius: 50%; }
.info { flex: 1; min-width: 200px; }
h1 { margin: 0 0 6px; font-size: 26px; }
.meta { display: flex; flex-wrap: wrap; gap: 14px; margin: 0 0 4px; font-size: 14px; font-weight: 600; }
.verified { color: var(--color-teal); }
.verified-badge { display: inline-grid; place-items: center; width: 22px; height: 22px; color: #fff; background: #1687f8; border-radius: 50%; font-size: 14px; vertical-align: 3px; }
.on { color: var(--color-success); }
.off { color: var(--color-muted); }
.rating { margin: 0; color: var(--color-muted); }
.panel { padding: 22px; margin-bottom: 20px; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-lg); }
.panel h2 { margin-top: 0; font-size: 20px; }
.skills { display: grid; gap: 12px; margin: 0; padding: 0; list-style: none; }
.skills li { display: flex; flex-wrap: wrap; align-items: center; gap: 10px; }
.s-icon { display: grid; place-items: center; width: 36px; height: 36px; background: var(--color-primary-soft); border-radius: 10px; }
.muted { color: var(--color-muted); }
</style>

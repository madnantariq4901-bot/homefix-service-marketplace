<script setup lang="ts">
import { getCategoryMeta } from "~/utils/categoryMeta"
import { categoriesService } from "~/services/categories.service"

const route = useRoute()
const authStore = useAuthStore()
const currency = useRuntimeConfig().public.currencySymbol
const serviceName = computed(() => String(route.params.service))
const { data: categories, pending, error } = await useAsyncData(
  `service-category-${serviceName.value}`,
  () => categoriesService.getCategories()
)
const category = computed(() => categories.value?.find(item => item.name === serviceName.value))
const meta = computed(() => getCategoryMeta(serviceName.value))

useHead(() => ({ title: category.value ? meta.value.label : "Service details" }))
</script>

<template>
  <main>
    <AppLoader v-if="pending && !category" />
    <section v-else-if="category" class="service-page">
      <div class="container">
        <NuxtLink to="/categories" class="back-link">← All services</NuxtLink>
        <div class="service-hero">
          <div class="service-copy">
            <p class="eyebrow"><span>{{ meta.icon }}</span> Home services</p>
            <h1>{{ meta.label }}</h1>
            <p class="lead">{{ category.description || meta.tagline }}</p>
            <p class="rate">From <strong>{{ currency }}{{ category.base_hourly_rate }}</strong> per hour</p>
            <div class="actions">
              <NuxtLink v-if="authStore.user?.role === 'provider'" to="/jobs" class="btn btn-accent">Find matching jobs <span aria-hidden="true">→</span></NuxtLink>
              <NuxtLink v-else-if="authStore.user?.role === 'admin'" to="/jobs" class="btn btn-accent">Manage jobs <span aria-hidden="true">→</span></NuxtLink>
              <NuxtLink v-else :to="`/jobs/create?category=${category.id}`" class="btn btn-accent">Request this service <span aria-hidden="true">→</span></NuxtLink>
              <NuxtLink v-if="authStore.user?.role !== 'provider' && authStore.user?.role !== 'admin'" :to="`/providers/browse?category=${category.name}`" class="btn btn-outline light-outline">Find a provider</NuxtLink>
            </div>
          </div>
          <img :src="meta.image" :alt="`${meta.label} professional at work`" />
        </div>

        <section class="service-details">
          <div>
            <p class="eyebrow section-eyebrow">Popular requests</p>
            <h2>What can a {{ meta.label.toLowerCase() }} help with?</h2>
            <p class="details-copy">Tell us what you need, add your location, and compare responses from service providers before choosing how to proceed.</p>
          </div>
          <ul class="examples">
            <li v-for="example in meta.examples" :key="example"><span aria-hidden="true">✓</span>{{ example }}</li>
          </ul>
        </section>

        <section v-if="authStore.user?.role !== 'provider' && authStore.user?.role !== 'admin'" class="next-step">
          <div>
            <h2>Ready to get started?</h2>
            <p>Submit your request and receive quotes from providers who can help.</p>
          </div>
          <NuxtLink :to="`/jobs/create?category=${category.id}`" class="btn btn-primary">Post a {{ meta.label.toLowerCase() }} job</NuxtLink>
        </section>
        <section v-else class="next-step provider-next-step">
          <div>
            <h2>{{ authStore.user?.role === "provider" ? "Looking for work?" : "Marketplace tools" }}</h2>
            <p>{{ authStore.user?.role === "provider" ? "Browse open jobs that match your skills." : "Review jobs and manage service listings." }}</p>
          </div>
          <NuxtLink :to="authStore.user?.role === 'provider' ? '/jobs' : '/admin/services'" class="btn btn-primary">{{ authStore.user?.role === "provider" ? "Find matching jobs" : "Manage services" }}</NuxtLink>
        </section>
      </div>
    </section>
    <section v-else class="container section not-found">
      <AppAlert v-if="error" type="error">Unable to load service details. Please try again.</AppAlert>
      <template v-else>
        <h1 class="section-title">Service not found</h1>
        <p class="section-subtitle">This service may no longer be available.</p>
      </template>
      <NuxtLink to="/categories" class="btn btn-outline">Browse all services</NuxtLink>
    </section>
  </main>
</template>

<style scoped>
.service-page { padding: 26px 0 60px; }
.back-link { display: inline-block; margin-bottom: 18px; color: var(--color-primary); font-weight: 600; text-decoration: none; }
.service-hero { display: grid; grid-template-columns: 1fr 1fr; overflow: hidden; min-height: 390px; color: #fff; background: var(--color-dark); border-radius: 22px; }
.service-copy { align-self: center; padding: clamp(28px, 5vw, 60px); }
.eyebrow { display: flex; align-items: center; gap: 9px; margin: 0 0 14px; color: #ffc48d; font-size: 12px; font-weight: 700; letter-spacing: .15em; text-transform: uppercase; }
.eyebrow span { font-size: 20px; letter-spacing: 0; }
h1 { margin: 0 0 14px; color: #fff; font-size: clamp(38px, 5vw, 58px); line-height: 1.05; }
.lead { max-width: 480px; margin: 0; color: #dbe5f2; font-size: 18px; }
.rate { margin: 18px 0 24px; color: #dbe5f2; }
.rate strong { color: #fff; font-size: 21px; }
.actions { display: flex; flex-wrap: wrap; gap: 12px; }
.light-outline { color: #fff; border-color: rgb(255 255 255 / 55%); }
.light-outline:hover { color: var(--color-dark); background: #fff; }
.service-hero > img { width: 100%; height: 100%; min-height: 390px; object-fit: cover; }
.service-details { display: grid; grid-template-columns: 1.1fr 0.9fr; gap: 50px; align-items: center; padding: 58px 0; }
.section-eyebrow { color: var(--color-primary); }
.service-details h2, .next-step h2 { margin: 0 0 12px; font-size: clamp(25px, 3vw, 34px); line-height: 1.15; }
.details-copy, .next-step p { color: var(--color-muted); }
.examples { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; margin: 0; padding: 0; list-style: none; }
.examples li { display: flex; align-items: center; gap: 9px; min-height: 54px; padding: 12px; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius); }
.examples li span { color: var(--color-teal); font-weight: 800; }
.next-step { display: flex; justify-content: space-between; align-items: center; gap: 24px; padding: 26px 30px; background: var(--color-primary-soft); border-radius: var(--radius-lg); }
.next-step h2, .next-step p { margin-top: 0; margin-bottom: 4px; }
.not-found { min-height: 360px; }
@media (max-width: 760px) {
  .service-hero, .service-details { grid-template-columns: 1fr; }
  .service-hero > img { min-height: 240px; max-height: 320px; grid-row: 1; }
  .service-copy { padding: 28px; }
  .service-details { gap: 20px; padding: 40px 0; }
}
@media (max-width: 520px) {
  .examples { grid-template-columns: 1fr; }
  .next-step { align-items: flex-start; flex-direction: column; padding: 22px; }
}
</style>

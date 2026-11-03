<script setup lang="ts">
import { categoriesService } from "~/services/categories.service"

// Public page: anyone can browse services without signing in (GET /categories is public).
useHead({ title: "Services" })

const { data: categories, pending, error } = await useAsyncData(
  "services-page-categories",
  () => categoriesService.getCategories()
)
</script>

<template>
  <main>
    <section class="services-hero">
      <div class="container hero-content">
        <div>
          <p class="eyebrow">Services for every corner</p>
          <h1>Find the right help for your home.</h1>
          <p>Explore the services available through HomeFix, learn what each one covers, and request the help you need.</p>
          <NuxtLink to="/providers/browse" class="btn btn-accent">Meet local providers <span aria-hidden="true">→</span></NuxtLink>
        </div>
        <img
          src="https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?auto=format&fit=crop&w=1200&q=85"
          alt="Comfortable, sunlit home ready for professional care"
        />
      </div>
    </section>

    <section class="container section">
      <div class="section-heading">
        <div>
          <p class="eyebrow section-eyebrow">Choose a service</p>
          <h2 class="section-title">What can we help with?</h2>
          <p class="section-subtitle">Open a service to see details, common jobs, and your next steps.</p>
        </div>
      </div>
      <AppLoader v-if="pending" />
      <AppAlert v-else-if="error" type="error">Unable to load services. Please try again.</AppAlert>
      <AppAlert v-else-if="!categories?.length" type="info">No services are available yet.</AppAlert>
      <CategoryList v-else :categories="categories" />
    </section>
  </main>
</template>

<style scoped>
.services-hero { overflow: hidden; color: #fff; background: var(--color-dark); }
.hero-content { display: grid; grid-template-columns: 1fr 0.9fr; align-items: center; gap: clamp(32px, 6vw, 80px); min-height: 360px; padding-block: 50px; }
.hero-content > div { max-width: 580px; }
.eyebrow { margin: 0 0 12px; color: #ffc48d; font-size: 12px; font-weight: 700; letter-spacing: .16em; text-transform: uppercase; }
h1 { margin: 0 0 14px; color: #fff; font-size: clamp(36px, 5vw, 56px); line-height: 1.08; letter-spacing: -.03em; }
.hero-content p:not(.eyebrow) { max-width: 520px; margin: 0 0 24px; color: #dbe5f2; }
.hero-content img { width: 100%; height: 270px; object-fit: cover; border-radius: 20px; box-shadow: 0 24px 60px rgb(0 0 0 / 24%); }
.section { padding-top: 56px; }
.section-heading { margin-bottom: 26px; }
.section-subtitle { margin-bottom: 0; }
@media (max-width: 760px) {
  .hero-content { grid-template-columns: 1fr; padding-block: 40px; }
  .hero-content img { height: 220px; }
}
</style>

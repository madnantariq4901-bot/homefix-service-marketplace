<script setup lang="ts">
import type { CategoryName } from "~/types/category"
import { providersService } from "~/services/provider.service"
import { getCategoryMeta } from "~/utils/categoryMeta"
import { categoriesService } from "~/services/categories.service"

// Public directory of providers with a marketplace badge (GET /providers/public).
useHead({ title: "Find a provider" })

const category = ref<CategoryName | "">("")
const availableOnly = ref(false)
const search = ref("")
const sort = ref<"recommended" | "completed_jobs" | "rating" | "experience" | "name">("recommended")
const page = ref(1)
const pageSize = 9
const route = useRoute()
const categoriesStore = useCategoriesStore()
const requestedCategory = typeof route.query.category === "string"
  ? categories.value?.find(item => item.name === route.query.category)?.name
  : undefined
if (requestedCategory) category.value = requestedCategory

const searchForRequest = ref("")
let searchTimer: ReturnType<typeof setTimeout> | undefined

const { data: categories } = await useAsyncData(
  "provider-directory-categories",
  () => categoriesService.getCategories()
)
categoriesStore.categories = categories.value ?? []

const { data: providerPage, pending, error } = await useAsyncData(
  "public-providers-directory",
  () => providersService.getPublicProviders({
    limit: pageSize + 1,
    offset: (page.value - 1) * pageSize,
    ...(category.value ? { category: category.value } : {}),
    ...(availableOnly.value ? { available_only: true } : {}),
    ...(searchForRequest.value ? { search: searchForRequest.value } : {}),
    sort_by: sort.value,
  }),
  { watch: [category, availableOnly, searchForRequest, sort, page] }
)

const options = computed(() => (categories.value ?? []).map(({ name }) => ({ name, ...getCategoryMeta(name) })))
const visibleProviders = computed(() => (providerPage.value ?? []).slice(0, pageSize))
const hasNextPage = computed(() => (providerPage.value?.length ?? 0) > pageSize)

watch(search, (value) => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    searchForRequest.value = value.trim()
  }, 300)
})

onBeforeUnmount(() => clearTimeout(searchTimer))

watch([category, availableOnly, search, sort], () => {
  page.value = 1
})
</script>

<template>
  <main>
    <section class="directory-hero">
      <div class="container directory-hero-content">
        <div>
          <p class="eyebrow">Local skills, one place</p>
          <h1>Find a provider you can count on.</h1>
          <p>Explore provider profiles, check their service skills, and connect around the work you need done. A badge reflects marketplace status, not an automatic government-ID check.</p>
        </div>
        <img
          src="https://images.unsplash.com/photo-1621905251918-48416bd8575a?auto=format&fit=crop&w=1200&q=85"
          alt="A skilled home-service professional at work"
        />
      </div>
    </section>

    <section class="container section directory">
      <div class="directory-heading">
        <div>
          <p class="eyebrow section-eyebrow">Provider directory</p>
          <h2 class="section-title">Meet local providers</h2>
          <p class="section-subtitle">Search, filter or sort to find the right fit.</p>
        </div>
        <NuxtLink to="/categories" class="text-link">Explore services <span aria-hidden="true">→</span></NuxtLink>
      </div>
      <div class="filters">
        <label class="grow">
          Search
          <input v-model="search" type="search" placeholder="Name or service" />
        </label>
        <label>
          Service
          <select v-model="category">
            <option value="">All services</option>
            <option v-for="option in options" :key="option.name" :value="option.name">{{ option.icon }} {{ option.label }}</option>
          </select>
        </label>
        <label>
          Sort by
          <select v-model="sort">
            <option value="recommended">Recommended</option>
            <option value="completed_jobs">Most completed jobs</option>
            <option value="rating">Top rated</option>
            <option value="experience">Most experienced</option>
            <option value="name">Name (A–Z)</option>
          </select>
        </label>
        <label class="check">
          <input v-model="availableOnly" type="checkbox" />
          Available now
        </label>
      </div>

      <p v-if="!pending && !error" class="result-count">
        Showing {{ visibleProviders.length }} {{ visibleProviders.length === 1 ? "provider" : "providers" }} on page {{ page }}
      </p>

      <AppLoader v-if="pending" />
      <AppAlert v-else-if="error" type="error">Unable to load providers. Please try again.</AppAlert>
      <AppAlert v-else-if="!visibleProviders.length" type="info">No providers match your filters yet.</AppAlert>
      <template v-else>
        <div class="grid">
          <PublicProviderCard v-for="provider in visibleProviders" :key="provider.id" :provider="provider" />
        </div>
        <nav v-if="page > 1 || hasNextPage" class="pager" aria-label="Pagination">
          <button type="button" class="btn btn-outline" :disabled="pending || page === 1" @click="page--">← Previous</button>
          <span>Page {{ page }}</span>
          <button type="button" class="btn btn-outline" :disabled="pending || !hasNextPage" @click="page++">Next →</button>
        </nav>
      </template>
    </section>
  </main>
</template>

<style scoped>
.directory-hero { overflow: hidden; color: #fff; background: var(--color-dark); }
.directory-hero-content { display: grid; grid-template-columns: 1fr .9fr; align-items: center; gap: clamp(32px, 6vw, 80px); min-height: 350px; padding-block: 46px; }
.directory-hero-content > div { max-width: 580px; }
.eyebrow { margin: 0 0 12px; color: #ffc48d; font-size: 12px; font-weight: 700; letter-spacing: .16em; text-transform: uppercase; }
.directory-hero h1 { margin: 0 0 14px; color: #fff; font-size: clamp(36px, 5vw, 54px); line-height: 1.08; }
.directory-hero-content p:not(.eyebrow) { max-width: 520px; margin: 0; color: #dbe5f2; font-size: 17px; }
.directory-hero img { width: 100%; height: 260px; object-fit: cover; border-radius: 18px; }
.directory { padding-top: 52px; }
.directory-heading { display: flex; justify-content: space-between; align-items: end; gap: 20px; margin-bottom: 24px; }
.section-eyebrow { color: var(--color-primary); }
.section-subtitle { margin-bottom: 0; }
.text-link { flex: 0 0 auto; color: var(--color-primary); font-weight: 700; text-decoration: none; }
.text-link span { margin-left: 6px; }
.filters { display: flex; flex-wrap: wrap; align-items: flex-end; gap: 20px; margin-bottom: 24px; }
.filters label { display: flex; flex-direction: column; gap: 6px; min-width: 220px; font-size: 14px; font-weight: 600; }
.filters .check { flex-direction: row; align-items: center; min-width: 0; padding-bottom: 10px; }
.filters .check input { width: auto; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }
@media (max-width: 760px) {
  .directory-hero-content { grid-template-columns: 1fr; padding-block: 38px; }
  .directory-hero img { height: 220px; }
  .directory-heading { align-items: flex-start; flex-direction: column; }
}
.filters .grow { flex: 1 1 240px; }
.result-count { margin: 0 0 14px; color: var(--color-muted); font-size: 14px; }
.pager { display: flex; align-items: center; justify-content: center; gap: 16px; margin-top: 28px; color: var(--color-muted); font-size: 14px; }
</style>

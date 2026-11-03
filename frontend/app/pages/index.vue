<script setup lang="ts">
import type { CategoryName } from "~/types/category"
import { apiErrorMessage } from "~/services/api"
import { providersService, type PublicProvider } from "~/services/provider.service"
import { reviewsService } from "~/services/reviews.service"
import { categoriesService } from "~/services/categories.service"

useHead({ title: "Home services, made simple" })

const authStore = useAuthStore()
const isProviderAccount = computed(() => authStore.user?.role === "provider")
const isAdminAccount = computed(() => authStore.user?.role === "admin")
const categoriesStore = useCategoriesStore()
const jobsStore = useJobsStore()
const serviceCategory = ref<CategoryName | "">("")
const description = ref("")
const address = ref("")
const latitude = ref<number | null>(null)
const longitude = ref<number | null>(null)
const bookingError = ref("")
const bookingNotice = ref("")
const bookingLoading = ref(false)
const bookingProviders = ref<PublicProvider[]>([])
const bookingProvidersLoading = ref(false)
const preferredProviderId = ref<number | null>(null)
const topProviders = ref<PublicProvider[]>([])
const stories = ref<{ id: number; rating: number; comment: string; providerName: string }[]>([])

const { data: initialCategories, error: initialCategoriesError } = await useAsyncData(
  "home-service-categories",
  () => categoriesService.getCategories()
)
categoriesStore.categories = initialCategories.value ?? []
categoriesStore.error = initialCategoriesError.value ? "Unable to load categories." : ""

async function loadCommunity() {
  try {
    const all = await providersService.getPublicProviders({ limit: 3 })
    topProviders.value = all.slice(0, 3)
    const rated = topProviders.value.filter(provider => provider.rating_count > 0)
    const batches = await Promise.all(
      rated.map(async (provider) => {
        const reviews = await reviewsService.getProviderReviews(provider.id)
        return reviews
          .filter(review => review.comment)
          .slice(0, 2)
          .map(review => ({
            id: review.id,
            rating: review.rating,
            comment: review.comment as string,
            providerName: provider.full_name,
          }))
      })
    )
    stories.value = batches.flat().slice(0, 3)
  } catch {
    // The home page keeps working without this section.
  }
}

onMounted(async () => {
  if (authStore.token && !authStore.user) await authStore.loadCurrentUser().catch(() => undefined)
  void loadCommunity()
})

const services: {
  name: CategoryName
  label: string
  description: string
  image: string
  alt: string
}[] = [
  {
    name: "cleaner",
    label: "Home Cleaning",
    description: "Routine, deep, and move-in cleaning",
    image: "https://images.unsplash.com/photo-1581578731548-c64695cc6952?auto=format&fit=crop&w=900&q=85",
    alt: "Professional cleaner tidying a bright home",
  },
  {
    name: "electrician",
    label: "Electrical Services",
    description: "Lighting, wiring, and electrical repairs",
    image: "https://images.unsplash.com/photo-1621905251918-48416bd8575a?auto=format&fit=crop&w=900&q=85",
    alt: "Electrician working on a home electrical installation",
  },
  {
    name: "plumber",
    label: "Plumbing",
    description: "Leaks, pipes, taps, and fittings",
    image: "https://images.unsplash.com/photo-1607472586893-edb57bdc0e39?auto=format&fit=crop&w=900&q=85",
    alt: "Plumbing tools ready for a home repair",
  },
  {
    name: "ac_technician",
    label: "AC Services",
    description: "Air conditioning repair and servicing",
    image: "https://images.unsplash.com/photo-1585771724684-38269d6639fd?auto=format&fit=crop&w=900&q=85",
    alt: "Air conditioning unit in a modern home",
  },
  {
    name: "carpenter",
    label: "Carpentry",
    description: "Furniture, doors, and woodwork",
    image: "https://images.unsplash.com/photo-1620626011761-996317b8d101?auto=format&fit=crop&w=900&q=85",
    alt: "Carpenter measuring a wooden surface",
  },
  {
    name: "painter",
    label: "Painting",
    description: "Interior walls and home touch-ups",
    image: "https://images.unsplash.com/photo-1562259949-e8e7689d7828?auto=format&fit=crop&w=900&q=85",
    alt: "Painter applying a fresh coat of paint to a wall",
  },
]

const availableServices = computed(() =>
  services.filter((service) => categoriesStore.categories.some((category) => category.name === service.name))
)
const unsupportedServices = computed(() =>
  categoriesStore.error
    ? []
    : services.filter((service) => !categoriesStore.categories.some((category) => category.name === service.name))
)

const steps = [
  { number: "01", title: "Tell us what you need", text: "Choose a service and describe the job and location." },
  { number: "02", title: "Review provider quotes", text: "Providers can respond to your request with a quote." },
  { number: "03", title: "Choose and follow the job", text: "Pick a quote and follow the job as its status updates." },
]

const reasons = [
  { icon: "01", title: "Your choice comes first", text: "Review the quotes you receive before choosing how to proceed." },
  { icon: "02", title: "Clear job details", text: "Describe the work and location upfront so providers understand your request." },
  { icon: "03", title: "Follow progress", text: "Check your job status and updates from your account." },
]

if (!serviceCategory.value && availableServices.value.length) {
  serviceCategory.value = availableServices.value[0].name
}

async function loadBookingProviders(categoryName: CategoryName | "") {
  const category = categoriesStore.categories.find(item => item.name === categoryName)
  if (!category) {
    bookingProviders.value = []
    preferredProviderId.value = null
    return
  }
  bookingProvidersLoading.value = true
  try {
    bookingProviders.value = await providersService.getPublicProviders({ category: category.name, limit: 100 })
  } catch {
    bookingProviders.value = []
  } finally {
    bookingProvidersLoading.value = false
  }
}

watch(serviceCategory, (categoryName) => {
  preferredProviderId.value = null
  void loadBookingProviders(categoryName)
})

onMounted(() => { void loadBookingProviders(serviceCategory.value) })

function onBookingLocationPicked(location: { address: string; latitude: number; longitude: number }) {
  address.value = location.address
  latitude.value = location.latitude
  longitude.value = location.longitude
}

function onBookingLocationCleared() {
  address.value = ""
  latitude.value = null
  longitude.value = null
}

function selectService(name: CategoryName) {
  bookingError.value = ""
  bookingNotice.value = ""
  if (isProviderAccount.value) return navigateTo(`/categories/${name}`)
  if (isAdminAccount.value) return navigateTo("/jobs")
  if (availableServices.value.some((service) => service.name === name)) {
    const category = categoriesStore.categories.find((item) => item.name === name)
    if (category) return navigateTo(`/jobs/create?category=${category.id}`)
  } else {
    bookingError.value = `${services.find((service) => service.name === name)?.label} is not currently available for online booking.`
    document.querySelector("#booking")?.scrollIntoView({ behavior: "smooth" })
  }
}

async function submitBooking() {
  bookingError.value = ""
  bookingNotice.value = ""
  if (
    !serviceCategory.value ||
    !description.value.trim() ||
    !address.value.trim() ||
    latitude.value === null ||
    longitude.value === null
  ) {
    bookingError.value = "Choose an available service, describe the job, and pin its location on the map."
    return
  }

  const category = categoriesStore.categories.find((item) => item.name === serviceCategory.value)
  if (!category) {
    bookingError.value = "That service is not currently available for online booking."
    return
  }

  if (!authStore.isAuthenticated) {
    await navigateTo({
      path: "/auth/login",
      query: { redirect: `/jobs/create?category=${category.id}` },
    })
    return
  }

  if (!authStore.user) {
    try {
      await authStore.loadCurrentUser()
    } catch {
      await navigateTo("/auth/login")
      return
    }
  }

  if (authStore.user?.role !== "customer") {
    bookingError.value = "Only customer accounts can create a service request."
    return
  }

  bookingLoading.value = true
  try {
    const job = await jobsStore.createJob({
      category_id: category.id,
      ...(preferredProviderId.value !== null ? { preferred_provider_id: preferredProviderId.value } : {}),
      description: description.value.trim(),
      address: address.value.trim(),
      lat: latitude.value,
      lng: longitude.value,
    })
    await navigateTo(`/jobs/${job.id}`)
  } catch (error: unknown) {
    bookingError.value = apiErrorMessage(error, jobsStore.error || "Unable to create your service request. Please try again.")
  } finally {
    bookingLoading.value = false
  }
}
</script>

<template>
  <main>
    <section class="hero">
      <div class="container hero-layout">
        <div class="hero-copy">
          <p class="eyebrow"><span /> Home services, made simple</p>
          <h1>Expert help for a home that <span>works beautifully.</span></h1>
          <p class="hero-description">
            Find the right service for your home, share what needs doing, and connect with local professionals.
          </p>
          <div class="hero-actions">
            <NuxtLink v-if="isProviderAccount" to="/jobs" class="btn btn-accent">Find matching jobs <span aria-hidden="true">→</span></NuxtLink>
            <NuxtLink v-else-if="isAdminAccount" to="/jobs" class="btn btn-accent">Manage jobs <span aria-hidden="true">→</span></NuxtLink>
            <NuxtLink v-else to="/jobs/create" class="btn btn-accent">Book a service <span aria-hidden="true">→</span></NuxtLink>
            <a href="#services" class="hero-link">Explore services <span aria-hidden="true">↓</span></a>
          </div>
          <div class="hero-points">
            <span><span class="check">✓</span> Straightforward job requests</span>
            <span><span class="check">✓</span> Quotes before you choose</span>
          </div>
        </div>
        <div class="hero-visual" role="img" aria-label="Bright, welcoming modern home interior">
          <div class="hero-image" />
          <div class="hero-caption">
            <span class="caption-mark" aria-hidden="true">⌂</span>
            <span><strong>Home care, made easier</strong><small>Start with the service you need</small></span>
          </div>
          <span class="hero-orbit orbit-one" />
          <span class="hero-orbit orbit-two" />
        </div>
      </div>
      <div class="hero-bottom" />
    </section>

    <section id="services" class="section container services-section">
      <div class="section-heading">
        <div>
          <p class="eyebrow section-eyebrow">Services for every corner</p>
          <h2 class="section-title">How can we help at home?</h2>
          <p class="section-subtitle">Explore the services available through HomeFix.</p>
        </div>
        <NuxtLink to="/categories" class="text-link">View all services <span aria-hidden="true">→</span></NuxtLink>
      </div>
      <div class="services-grid">
        <article v-for="(service, index) in services" :key="service.name" class="service-card">
          <NuxtLink class="service-image-button" :to="`/categories/${service.name}`" :aria-label="`Explore ${service.label}`">
            <img :src="service.image" :alt="service.alt" loading="lazy" />
            <span class="service-number">{{ String(index + 1).padStart(2, "0") }}</span>
          </NuxtLink>
          <div class="service-content">
            <h3>{{ service.label }}</h3>
            <p>{{ service.description }}</p>
            <button class="service-link" type="button" @click="selectService(service.name)">
              {{ isProviderAccount ? "Explore service" : isAdminAccount ? "View marketplace jobs" : availableServices.some((item) => item.name === service.name) ? "Book this service" : "Explore service" }}
              <span aria-hidden="true">↗</span>
            </button>
          </div>
        </article>
      </div>
      <p v-if="categoriesStore.loading" class="availability-note">Checking service availability…</p>
      <p v-else-if="categoriesStore.error" class="availability-note" role="status">
        Service availability could not be loaded. You can still explore the categories.
      </p>
    </section>

    <section v-if="isProviderAccount" id="booking" class="booking-section">
      <div class="container booking-layout role-actions-layout">
        <div class="booking-intro">
          <p class="eyebrow">Service-provider workspace</p>
          <h2>Find work that fits your skills.</h2>
          <p>Browse matching requests, manage your profile, and keep your service details up to date.</p>
        </div>
        <div class="role-actions">
          <NuxtLink to="/jobs" class="btn btn-accent">Explore matching jobs</NuxtLink>
          <NuxtLink to="/providers" class="btn btn-light">Manage provider profile</NuxtLink>
        </div>
      </div>
    </section>

    <section v-else-if="isAdminAccount" id="booking" class="booking-section">
      <div class="container booking-layout role-actions-layout">
        <div class="booking-intro">
          <p class="eyebrow">Marketplace administration</p>
          <h2>Keep the marketplace moving.</h2>
          <p>Review jobs, approach providers, and manage the services customers can request.</p>
        </div>
        <div class="role-actions">
          <NuxtLink to="/jobs" class="btn btn-accent">Manage jobs</NuxtLink>
          <NuxtLink to="/admin/services" class="btn btn-light">Manage services</NuxtLink>
        </div>
      </div>
    </section>

    <section v-else-if="authStore.user?.role === 'customer'" id="booking" class="booking-section">
      <div class="container booking-layout">
        <div class="booking-intro">
          <p class="eyebrow">A few details to get started</p>
          <h2>Let’s take care of your to-do list.</h2>
          <p>Tell us what needs doing and where. Your request is sent to the HomeFix service marketplace.</p>
          <div class="booking-promise"><span aria-hidden="true">✓</span> No payment is collected by this request form.</div>
        </div>
        <form class="booking-card" @submit.prevent="submitBooking">
          <div class="form-heading">
            <span class="form-icon" aria-hidden="true">⌂</span>
            <div><h3>Request a service</h3><p>Share a few details about the job.</p></div>
          </div>
          <label for="booking-service">Service needed</label>
          <select id="booking-service" v-model="serviceCategory" required :disabled="categoriesStore.loading || !availableServices.length">
            <option value="" disabled>Select a service</option>
            <option v-for="service in availableServices" :key="service.name" :value="service.name">{{ service.label }}</option>
          </select>
          <label for="booking-provider">Preferred provider (optional)</label>
          <select id="booking-provider" v-model.number="preferredProviderId" :disabled="bookingProvidersLoading || !bookingProviders.length">
            <option :value="null">Open to any matching provider</option>
            <option v-for="provider in bookingProviders" :key="provider.id" :value="provider.id">
              {{ provider.full_name }} · {{ provider.completed_job_count }} completed jobs{{ provider.is_available ? " · Available" : "" }}
            </option>
          </select>
          <p v-if="bookingProvidersLoading" class="form-hint">Finding providers for this service…</p>
          <p v-else-if="bookingProviders.length" class="form-hint">A selected provider is invited first; the job is not assigned until you accept their quote.</p>
          <p v-if="unsupportedServices.length && !categoriesStore.loading" class="form-hint">
            Online booking is not yet available for: {{ unsupportedServices.map((service) => service.label).join(", ") }}.
          </p>
          <label for="booking-description">What do you need help with?</label>
          <textarea id="booking-description" v-model="description" rows="3" minlength="3" maxlength="2000" placeholder="Briefly describe the work you need…" required />
          <label>Service address and map pin</label>
          <ClientOnly>
            <AddressMapPicker @picked="onBookingLocationPicked" @cleared="onBookingLocationCleared" />
          </ClientOnly>
          <p v-if="!authStore.isAuthenticated" class="form-hint">Sign in to submit a service request.</p>
          <AppAlert v-if="bookingNotice" type="success">{{ bookingNotice }}</AppAlert>
          <AppAlert v-if="bookingError || categoriesStore.error" type="error">
            {{ bookingError || categoriesStore.error }}
          </AppAlert>
          <button class="btn btn-primary booking-submit" type="submit" :disabled="bookingLoading || categoriesStore.loading || !availableServices.length">
            {{ bookingLoading ? "Sending request…" : authStore.isAuthenticated ? "Submit service request" : "Sign in to continue" }}
            <span aria-hidden="true">→</span>
          </button>
          <p class="form-footnote">Your request is submitted only after the backend confirms it.</p>
        </form>
      </div>
    </section>

    <section v-else id="booking" class="booking-section">
      <div class="container booking-layout role-actions-layout">
        <div class="booking-intro">
          <p class="eyebrow">Get started with HomeFix</p>
          <h2>Sign in to request a service.</h2>
          <p>You can explore services and providers before signing in. Sign in when you’re ready to post a job.</p>
        </div>
        <div class="role-actions">
          <NuxtLink to="/jobs/create" class="btn btn-accent">Sign in to request a service</NuxtLink>
          <NuxtLink to="/auth/login?redirect=%2Fproviders&role=provider" class="btn btn-light">Join as a provider</NuxtLink>
        </div>
      </div>
    </section>

    <section class="section container about-section">
      <div class="about-image">
        <img
          src="https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?auto=format&fit=crop&w=1200&q=85"
          alt="Comfortable, sunlit living room"
          loading="lazy"
        />
        <div class="about-image-label"><span>⌂</span> Made for the place you call home</div>
      </div>
      <div class="about-copy">
        <p class="eyebrow section-eyebrow">A better way to get things done</p>
        <h2>Your home deserves thoughtful care.</h2>
        <p>HomeFix brings service requests, provider quotes, and job updates together in one place. Start with what you need, then choose how to move forward.</p>
        <NuxtLink to="/about" class="btn btn-outline">More about HomeFix <span aria-hidden="true">→</span></NuxtLink>
        <div class="about-detail">
          <span aria-hidden="true">✳</span>
          <p><strong>Practical help, on your terms.</strong><br />Describe the work before deciding on a provider or quote.</p>
        </div>
      </div>
    </section>

    <section v-if="topProviders.length" class="section container top-providers">
      <div class="section-heading">
        <div>
          <p class="eyebrow section-eyebrow">Verified professionals</p>
          <h2 class="section-title">Top-rated providers</h2>
        </div>
        <NuxtLink to="/providers/browse" class="text-link">See all providers <span aria-hidden="true">→</span></NuxtLink>
      </div>
      <div class="provider-grid">
        <PublicProviderCard v-for="provider in topProviders" :key="provider.id" :provider="provider" />
      </div>
    </section>

    <section class="steps-section section">
      <div class="container">
        <div class="center-heading">
          <p class="eyebrow section-eyebrow">Simple from start to finish</p>
          <h2 class="section-title">How HomeFix works</h2>
          <p class="section-subtitle">A clear path from a home to-do to a completed job.</p>
        </div>
        <ol class="steps-grid">
          <li v-for="step in steps" :key="step.number" class="step-card">
            <span class="step-number">{{ step.number }}</span>
            <span class="step-icon" aria-hidden="true">{{ step.number === "01" ? "✎" : step.number === "02" ? "⌕" : "✓" }}</span>
            <h3>{{ step.title }}</h3>
            <p>{{ step.text }}</p>
          </li>
        </ol>
      </div>
    </section>

    <section class="section container why-section">
      <div class="why-heading">
        <p class="eyebrow section-eyebrow">Why HomeFix</p>
        <h2 class="section-title">Confidence in every step.</h2>
        <p class="section-subtitle">Helpful tools to keep your service request clear and in your hands.</p>
        <NuxtLink to="/categories" class="text-link">Find your service <span aria-hidden="true">→</span></NuxtLink>
      </div>
      <div class="reasons-grid">
        <article v-for="reason in reasons" :key="reason.title" class="reason-card">
          <span class="reason-icon">{{ reason.icon }}</span>
          <h3>{{ reason.title }}</h3>
          <p>{{ reason.text }}</p>
        </article>
      </div>
    </section>

    <section class="testimonials-section section">
      <div class="container testimonial-inner">
        <div class="center-heading">
          <p class="eyebrow section-eyebrow">The HomeFix community</p>
          <h2 class="section-title">Customer stories</h2>
          <p class="section-subtitle">We only share feedback submitted through completed jobs.</p>
        </div>
        <div v-if="stories.length" class="story-grid">
          <figure v-for="story in stories" :key="story.id" class="story-card">
            <div class="story-stars" :aria-label="`${story.rating} out of 5 stars`">{{ "★".repeat(story.rating) }}{{ "☆".repeat(5 - story.rating) }}</div>
            <blockquote>{{ story.comment }}</blockquote>
            <figcaption>About {{ story.providerName }}</figcaption>
          </figure>
        </div>
        <div v-else class="testimonial-empty" role="status">
          <span aria-hidden="true">“</span>
          <p>Customer stories will appear here when verified reviews are available.</p>
        </div>
      </div>
    </section>

    <section class="container final-cta">
      <div><p class="eyebrow">{{ isProviderAccount ? "Your provider workspace" : isAdminAccount ? "Marketplace administration" : "Your next home project starts here" }}</p><h2>{{ isProviderAccount ? "Ready to find your next job?" : isAdminAccount ? "Ready to manage the marketplace?" : "Ready to get started?" }}</h2><p>{{ isProviderAccount ? "Review open requests that match your skills." : isAdminAccount ? "Review requests and service listings." : "Choose a service and tell us what you need." }}</p></div>
      <NuxtLink :to="isProviderAccount || isAdminAccount ? '/jobs' : '/jobs/create'" class="btn btn-accent">{{ isProviderAccount ? "Find matching jobs" : isAdminAccount ? "Manage jobs" : "Request a service" }} <span aria-hidden="true">→</span></NuxtLink>
    </section>
  </main>
</template>

<style scoped>
.hero { position: relative; overflow: hidden; color: #fff; background: var(--color-dark); }
.hero-layout { display: grid; grid-template-columns: 1.02fr 0.98fr; align-items: center; gap: clamp(36px, 6vw, 84px); min-height: 570px; padding-block: 58px 76px; }
.hero-copy { position: relative; z-index: 1; max-width: 610px; }
.eyebrow { display: flex; align-items: center; gap: 10px; margin: 0 0 18px; color: #ffc48d; font-size: 12px; font-weight: 700; letter-spacing: .16em; text-transform: uppercase; }
.eyebrow > span { width: 25px; height: 2px; background: var(--color-accent); }
h1 { max-width: 620px; margin: 0 0 20px; color: #fff; font-size: clamp(42px, 5.6vw, 68px); line-height: 1.06; font-weight: 750; letter-spacing: -.045em; }
h1 span { color: #9db5ff; }
.hero-description { max-width: 490px; margin: 0; color: #c5d0e3; font-size: 17px; line-height: 1.75; }
.hero-actions { display: flex; align-items: center; flex-wrap: wrap; gap: 27px; margin-top: 30px; }
.hero-actions .btn { min-height: 50px; padding-inline: 22px; }
.hero-link { color: #fff; font-weight: 600; text-decoration: none; }
.hero-link span { margin-left: 7px; color: #a9baff; }
.hero-points { display: flex; flex-wrap: wrap; gap: 12px 24px; margin-top: 36px; color: #d4ddec; font-size: 13px; }
.check { display: inline-grid; place-items: center; width: 19px; height: 19px; margin-right: 5px; color: #fff; background: #244de4; border-radius: 50%; font-size: 11px; }
.hero-visual { position: relative; min-height: 400px; }
.hero-image { position: absolute; inset: 5px 10px 5px 20px; background: url("https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?auto=format&fit=crop&w=1400&q=90") center/cover; border-radius: 48% 14px 14px 14px; box-shadow: 0 28px 70px rgb(0 0 0 / 28%); }
.hero-image::after { position: absolute; inset: 0; content: ""; background: linear-gradient(180deg, transparent 55%, rgb(9 25 50 / 42%)); border-radius: inherit; }
.hero-caption { position: absolute; z-index: 2; right: -6px; bottom: 25px; display: flex; align-items: center; gap: 13px; padding: 16px 20px; color: var(--color-dark); background: #fff; border-radius: 12px; box-shadow: var(--shadow-md); }
.hero-caption strong, .hero-caption small { display: block; }
.hero-caption strong { font-size: 14px; }
.hero-caption small { margin-top: 3px; color: var(--color-muted); font-size: 12px; }
.caption-mark { display: grid; place-items: center; width: 40px; height: 40px; color: #fff; background: var(--color-primary); border-radius: 10px; font-size: 23px; }
.hero-orbit { position: absolute; z-index: 1; width: 66px; height: 66px; border: 1px solid rgb(255 255 255 / 24%); border-radius: 50%; }
.orbit-one { top: -15px; right: 14px; }
.orbit-two { top: 2px; right: -3px; width: 32px; height: 32px; background: var(--color-accent); border: 0; }
.hero-bottom { position: absolute; right: 0; bottom: 0; left: 0; height: 9px; background: linear-gradient(90deg, var(--color-primary) 0 66%, var(--color-accent) 66%); }
.section { padding-block: 86px; }
.services-section { padding-bottom: 90px; }
.section-heading { display: flex; align-items: end; justify-content: space-between; gap: 25px; margin-bottom: 30px; }
.section-eyebrow { margin-bottom: 12px; color: var(--color-primary); }
.section-title { margin: 0 0 9px; color: var(--color-dark); font-size: clamp(28px, 3.5vw, 39px); font-weight: 750; letter-spacing: -.035em; }
.section-subtitle { margin: 0; color: var(--color-muted); font-size: 15px; }
.text-link { flex: 0 0 auto; padding-bottom: 6px; color: var(--color-primary); font-weight: 700; text-decoration: none; }
.text-link span { padding-left: 7px; }
.services-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 20px; }
.service-card { overflow: hidden; background: #fff; border: 1px solid #e9edf4; border-radius: 14px; box-shadow: 0 7px 22px rgb(20 43 80 / 5%); transition: transform .2s ease, box-shadow .2s ease; }
.service-card:hover { transform: translateY(-4px); box-shadow: 0 16px 34px rgb(20 43 80 / 12%); }
.service-image-button { position: relative; display: block; width: 100%; height: 185px; padding: 0; overflow: hidden; background: #e8edf6; border: 0; border-radius: 0; }
.service-image-button:hover:not(:disabled) { transform: none; box-shadow: none; }
.service-image-button img { width: 100%; height: 100%; object-fit: cover; transition: transform .4s ease; }
.service-card:hover img { transform: scale(1.04); }
.service-number { position: absolute; right: 13px; bottom: 13px; display: grid; place-items: center; width: 37px; height: 37px; color: #fff; background: rgb(20 43 80 / 82%); border: 1px solid rgb(255 255 255 / 35%); border-radius: 50%; font-size: 12px; font-weight: 700; }
.service-content { padding: 18px 19px 20px; }
.service-content h3 { margin: 0 0 5px; color: var(--color-dark); font-size: 18px; }
.service-content p { min-height: 42px; margin: 0; color: var(--color-muted); font-size: 13px; }
.service-link { display: flex; justify-content: space-between; width: 100%; margin-top: 13px; padding: 11px 0 0; color: var(--color-primary); background: none; border: 0; border-top: 1px solid #edf0f5; border-radius: 0; font-size: 13px; font-weight: 700; text-align: left; }
.service-link:hover:not(:disabled) { color: var(--color-accent); background: none; box-shadow: none; transform: none; }
.availability-note { margin: 18px 0 0; color: var(--color-muted); font-size: 13px; }
.booking-section { position: relative; overflow: hidden; padding-block: 86px; color: #fff; background: #142b50; }
.booking-section::before { position: absolute; top: -220px; left: -130px; width: 450px; height: 450px; content: ""; border: 1px solid rgb(255 255 255 / 9%); border-radius: 50%; box-shadow: 0 0 0 55px rgb(255 255 255 / 2%), 0 0 0 110px rgb(255 255 255 / 2%); }
.booking-layout { position: relative; z-index: 1; display: grid; grid-template-columns: .85fr 1.15fr; align-items: center; gap: clamp(40px, 9vw, 115px); }
.role-actions-layout { grid-template-columns: 1fr auto; }
.role-actions { display: flex; flex-wrap: wrap; gap: 12px; }
.booking-intro .eyebrow { color: #ffc48d; }
.booking-intro h2 { max-width: 480px; margin: 0 0 17px; color: #fff; font-size: clamp(34px, 4vw, 48px); line-height: 1.12; letter-spacing: -.04em; }
.booking-intro > p:not(.eyebrow) { max-width: 430px; margin: 0; color: #c5d0e3; line-height: 1.75; }
.booking-promise { margin-top: 26px; color: #dce5f3; font-size: 13px; }
.booking-promise span { display: inline-grid; place-items: center; width: 20px; height: 20px; margin-right: 7px; color: #fff; background: var(--color-primary); border-radius: 50%; }
.booking-card { padding: clamp(22px, 4vw, 36px); color: var(--color-dark); background: #fff; border-radius: 16px; box-shadow: 0 20px 50px rgb(0 0 0 / 20%); }
.form-heading { display: flex; align-items: center; gap: 13px; margin-bottom: 22px; }
.form-icon { display: grid; place-items: center; width: 46px; height: 46px; color: #fff; background: var(--color-primary); border-radius: 12px; font-size: 25px; }
.form-heading h3 { margin: 0; font-size: 20px; }
.form-heading p { margin: 3px 0 0; color: var(--color-muted); font-size: 13px; }
.booking-card label { display: block; margin: 15px 0 7px; color: var(--color-dark); font-size: 13px; font-weight: 700; }
.booking-card input, .booking-card select, .booking-card textarea { background: #fbfcfe; border-color: #e1e7f0; border-radius: 8px; font-size: 14px; }
.booking-card textarea { min-height: 82px; resize: vertical; }
.form-hint, .form-footnote { margin: 7px 0 0; color: var(--color-muted); font-size: 12px; }
.booking-submit { display: flex; width: 100%; min-height: 49px; margin-top: 19px; }
.booking-submit span { margin-left: auto; }
.form-footnote { text-align: center; }
.about-section { display: grid; grid-template-columns: 1fr 1fr; align-items: center; gap: clamp(40px, 8vw, 105px); }
.about-image { position: relative; min-height: 400px; }
.about-image img { width: 100%; height: 400px; object-fit: cover; border-radius: 15px 100px 15px 15px; }
.about-image-label { position: absolute; right: -20px; bottom: 25px; display: flex; align-items: center; gap: 10px; padding: 14px 18px; color: var(--color-dark); background: #fff; border-radius: 9px; box-shadow: var(--shadow-md); font-size: 13px; font-weight: 700; }
.about-image-label span { color: var(--color-accent); font-size: 23px; }
.about-copy h2 { max-width: 440px; margin: 0 0 17px; color: var(--color-dark); font-size: clamp(31px, 3.5vw, 43px); line-height: 1.12; letter-spacing: -.035em; }
.about-copy > p:not(.eyebrow) { margin: 0 0 23px; color: var(--color-muted); line-height: 1.8; }
.about-copy .btn { min-height: 46px; }
.about-detail { display: flex; align-items: flex-start; gap: 13px; margin-top: 30px; padding-top: 22px; border-top: 1px solid #e5eaf2; }
.about-detail > span { color: var(--color-accent); font-size: 23px; }
.about-detail p { margin: 0; color: var(--color-muted); font-size: 13px; line-height: 1.7; }
.about-detail strong { color: var(--color-dark); }
.steps-section { background: #fff; }
.center-heading { margin: 0 auto 37px; text-align: center; }
.center-heading .eyebrow { justify-content: center; }
.steps-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 22px; margin: 0; padding: 0; list-style: none; }
.step-card { position: relative; min-height: 235px; padding: 29px 25px; background: #f8faff; border: 1px solid #e9eef7; border-radius: 13px; }
.step-number { position: absolute; top: 22px; right: 23px; color: #b3bfda; font-size: 13px; font-weight: 800; letter-spacing: .08em; }
.step-icon { display: grid; place-items: center; width: 49px; height: 49px; margin-bottom: 23px; color: #fff; background: var(--color-primary); border-radius: 13px; font-size: 24px; }
.step-card:nth-child(2) .step-icon { background: var(--color-accent); }
.step-card h3 { margin: 0 0 9px; color: var(--color-dark); font-size: 18px; }
.step-card p { max-width: 290px; margin: 0; color: var(--color-muted); font-size: 14px; line-height: 1.7; }
.why-section { display: grid; grid-template-columns: .8fr 1.2fr; align-items: center; gap: 55px; }
.why-heading .section-subtitle { max-width: 360px; margin-bottom: 19px; line-height: 1.7; }
.reasons-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 13px; }
.reason-card { min-height: 205px; padding: 21px 17px; background: #fff; border: 1px solid #e9edf4; border-radius: 12px; }
.reason-icon { display: inline-grid; place-items: center; width: 36px; height: 36px; margin-bottom: 19px; color: var(--color-primary); background: #edf2ff; border-radius: 10px; font-size: 11px; font-weight: 800; }
.reason-card h3 { margin: 0 0 7px; color: var(--color-dark); font-size: 15px; }
.reason-card p { margin: 0; color: var(--color-muted); font-size: 12px; line-height: 1.65; }
.testimonials-section { background: #fff; }
.testimonial-inner { max-width: 1040px; }
.testimonial-empty { display: grid; justify-items: center; padding: 27px; color: var(--color-muted); background: #f8faff; border: 1px dashed #d8e0ee; border-radius: 13px; text-align: center; }
.testimonial-empty > span { height: 45px; color: var(--color-primary); font-family: Georgia, serif; font-size: 66px; line-height: 1; }
.testimonial-empty p { margin: 5px 0 0; font-size: 14px; }
.final-cta { display: flex; align-items: center; justify-content: space-between; gap: 25px; margin-bottom: 5px; padding: 38px clamp(25px, 5vw, 60px); color: #fff; background: var(--color-primary); border-radius: 16px; }
.final-cta .eyebrow { margin-bottom: 7px; color: #b8c9ff; }
.final-cta h2 { margin: 0 0 5px; font-size: 27px; letter-spacing: -.025em; }
.final-cta p:last-child { margin: 0; color: #d2dcf3; font-size: 14px; }
.final-cta .btn { flex: 0 0 auto; min-height: 47px; }
@media (max-width: 900px) {
  .hero-layout { grid-template-columns: 1fr .8fr; gap: 25px; min-height: 520px; }
  .hero-visual { min-height: 350px; }
  .booking-layout { gap: 40px; }
  .why-section { grid-template-columns: 1fr; gap: 30px; }
}
@media (max-width: 700px) {
  .hero-layout { grid-template-columns: 1fr; gap: 34px; padding-block: 58px 60px; }
  h1 { max-width: 560px; font-size: clamp(39px, 10vw, 57px); }
  .hero-visual { width: min(100%, 500px); min-height: 300px; margin-inline: auto; }
  .hero-image { inset: 0 12px 0 8px; border-top-left-radius: 105px; }
  .hero-caption { right: -2px; bottom: 12px; }
  .section { padding-block: 65px; }
  .section-heading { align-items: flex-start; flex-direction: column; gap: 13px; }
  .services-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 13px; }
  .service-image-button { height: 150px; }
  .service-content { padding: 15px; }
  .service-content h3 { font-size: 16px; }
  .service-content p { min-height: 40px; font-size: 12px; }
  .booking-layout, .about-section { grid-template-columns: 1fr; }
  .role-actions { align-items: stretch; flex-direction: column; }
  .booking-section { padding-block: 65px; }
  .booking-intro h2 { max-width: 560px; }
  .booking-card { margin-top: 4px; }
  .about-section { gap: 35px; }
  .about-image { min-height: 320px; }
  .about-image img { height: 320px; }
  .about-image-label { right: 8px; bottom: 14px; }
  .steps-grid { grid-template-columns: 1fr; gap: 13px; }
  .step-card { min-height: auto; padding: 23px; }
  .step-icon { margin-bottom: 16px; }
  .reasons-grid { grid-template-columns: 1fr; }
  .reason-card { min-height: auto; }
  .reason-icon { margin-bottom: 11px; }
  .final-cta { align-items: flex-start; flex-direction: column; margin-bottom: 0; padding-block: 30px; }
}
@media (max-width: 420px) {
  .hero-points { flex-direction: column; gap: 9px; }
  .hero-visual { min-height: 255px; }
  .services-grid { grid-template-columns: 1fr; }
  .service-image-button { height: 190px; }
}
.provider-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }
.story-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 18px; }
.story-card { display: flex; flex-direction: column; gap: 10px; margin: 0; padding: 22px; background: #f8faff; border: 1px solid var(--color-border); border-radius: var(--radius-lg); }
.story-stars { color: var(--color-accent); letter-spacing: 2px; }
.story-card blockquote { margin: 0; color: var(--color-text); line-height: 1.6; }
.story-card figcaption { margin-top: auto; color: var(--color-muted); font-size: 14px; font-weight: 600; }
</style>

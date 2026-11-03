<script setup lang="ts">
const authStore = useAuthStore()
useHead({ title: "About" })
const siteName = useRuntimeConfig().public.siteName
</script>

<template>
  <main class="container section about">
    <section class="about-hero">
      <div>
        <p class="eyebrow">About {{ siteName }}</p>
        <h1>Good work starts with a clear connection.</h1>
        <p>HomeFix brings service requests, provider quotes, and job updates together in one place.</p>
      </div>
      <img
        src="https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?auto=format&fit=crop&w=1200&q=85"
        alt="A cared-for, welcoming home"
      />
    </section>

    <div class="cols" :class="{ 'single-card': authStore.user }">
      <section v-if="!authStore.user || authStore.user.role === 'customer'">
        <img src="https://images.unsplash.com/photo-1581578731548-c64695cc6952?auto=format&fit=crop&w=900&q=85" alt="A professional caring for a home" loading="lazy" />
        <div class="card-copy">
          <h2>For customers</h2>
          <p>Post what you need, review quotes from providers, and follow the job status from your account. Once a job is completed, you can leave a review.</p>
          <NuxtLink to="/categories" class="btn btn-outline">Browse services</NuxtLink>
        </div>
      </section>
      <section v-if="!authStore.user">
        <img src="https://images.unsplash.com/photo-1621905251918-48416bd8575a?auto=format&fit=crop&w=900&q=85" alt="A skilled professional working on a home service" loading="lazy" />
        <div class="card-copy">
          <h2>For providers</h2>
          <p>Create a profile, list your skills, and set your availability. Providers can review matching job requests and submit quotes through the platform.</p>
          <NuxtLink to="/auth/login?redirect=%2Fproviders&role=provider" class="btn btn-outline">Join as a provider</NuxtLink>
        </div>
      </section>
      <section v-if="authStore.user?.role === 'provider'">
        <img src="https://images.unsplash.com/photo-1621905251918-48416bd8575a?auto=format&fit=crop&w=900&q=85" alt="A skilled professional working on a home service" loading="lazy" />
        <div class="card-copy">
          <h2>Your provider workspace</h2>
          <p>Update your service skills, availability, and work location, then review matching job requests.</p>
          <NuxtLink to="/providers" class="btn btn-outline">Manage provider profile</NuxtLink>
          <NuxtLink to="/jobs" class="btn btn-outline">Find matching jobs</NuxtLink>
        </div>
      </section>
      <section v-if="authStore.user?.role === 'admin'">
        <img src="https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?auto=format&fit=crop&w=900&q=85" alt="A well-maintained home" loading="lazy" />
        <div class="card-copy">
          <h2>Marketplace administration</h2>
          <p>Review customer jobs, approach providers, and manage the available services.</p>
          <NuxtLink to="/jobs" class="btn btn-outline">Manage jobs</NuxtLink>
          <NuxtLink to="/admin/services" class="btn btn-outline">Manage services</NuxtLink>
        </div>
      </section>
    </div>
  </main>
</template>

<style scoped>
.about { padding-top: 38px; }
.about-hero { display: grid; grid-template-columns: 1fr 1fr; align-items: center; gap: 42px; margin-bottom: 36px; }
.about-hero h1 { margin: 0 0 14px; font-size: clamp(34px, 4.5vw, 52px); line-height: 1.1; }
.about-hero p:not(.eyebrow) { max-width: 520px; color: var(--color-muted); font-size: 18px; }
.eyebrow { margin: 0 0 12px; color: var(--color-primary); font-size: 12px; font-weight: 700; letter-spacing: .15em; text-transform: uppercase; }
.about-hero img { width: 100%; height: 300px; object-fit: cover; border-radius: 18px; }
.cols { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 20px; }
.cols.single-card { grid-template-columns: minmax(0, 720px); }
section:not(.about-hero) { overflow: hidden; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-lg); }
.cols img { width: 100%; height: 190px; object-fit: cover; }
.card-copy { padding: 22px; }
h2 { margin-top: 0; }
.card-copy p { color: var(--color-muted); }
@media (max-width: 720px) { .about-hero { grid-template-columns: 1fr; gap: 20px; } .about-hero img { height: 230px; } .cols { grid-template-columns: 1fr; } }
</style>

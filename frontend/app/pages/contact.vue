<script setup lang="ts">
useHead({ title: "Contact" })
const config = useRuntimeConfig().public
</script>

<template>
  <main class="container section contact">
    <section class="contact-hero">
      <img src="https://images.unsplash.com/photo-1521791136064-7986c2920216?auto=format&fit=crop&w=1000&q=85" alt="Customer support team ready to help" />
      <div>
        <p class="eyebrow">We are here to help</p>
        <h1>Let’s get your question answered.</h1>
        <p>Questions about a job, a provider, or your account? Reach our support team using the contact details below.</p>
      </div>
    </section>
    <div class="card">
      <h2>Talk to our team</h2>
      <p v-if="config.supportEmail"><strong>Email:</strong> <a :href="`mailto:${config.supportEmail}`">{{ config.supportEmail }}</a></p>
      <p v-if="config.supportPhone"><strong>Phone:</strong> <a :href="`tel:${config.supportPhone}`">{{ config.supportPhone }}</a></p>
      <NuxtLink to="/categories" class="btn btn-outline">Browse services</NuxtLink>
    </div>
  </main>
</template>

<style scoped>
.contact { max-width: 1060px; }
.contact-hero { display: grid; grid-template-columns: 0.9fr 1.1fr; align-items: center; gap: 42px; margin-bottom: 30px; }
.contact-hero img { width: 100%; height: 300px; object-fit: cover; border-radius: 18px; }
.eyebrow { margin: 0 0 12px; color: var(--color-primary); font-size: 12px; font-weight: 700; letter-spacing: .15em; text-transform: uppercase; }
h1 { margin: 0 0 12px; font-size: clamp(34px, 4vw, 48px); line-height: 1.1; }
.contact-hero p:not(.eyebrow) { color: var(--color-muted); font-size: 18px; }
.card { padding: 26px; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-lg); }
.card h2 { margin-top: 0; }
.card p { margin: 0 0 10px; }
.card .btn { margin-top: 10px; }
@media (max-width: 720px) { .contact-hero { grid-template-columns: 1fr; gap: 20px; } .contact-hero img { height: 230px; } }
</style>

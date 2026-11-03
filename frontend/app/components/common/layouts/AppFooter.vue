<script setup lang="ts">
import { categoryMeta } from "~/utils/categoryMeta"
import { getConfiguredSocialLinks } from "~/config/socialLinks"

const config = useRuntimeConfig().public
const year = new Date().getFullYear()
const services = [
  { slug: "cleaner", label: categoryMeta.cleaner?.label ?? "Home Cleaning" },
  { slug: "electrician", label: categoryMeta.electrician?.label ?? "Electrical Services" },
  { slug: "plumber", label: categoryMeta.plumber?.label ?? "Plumbing" },
  { slug: "ac_technician", label: categoryMeta.ac_technician?.label ?? "AC Services" },
  { slug: "carpenter", label: categoryMeta.carpenter?.label ?? "Carpentry" },
  { slug: "painter", label: categoryMeta.painter?.label ?? "Painting" },
]
</script>

<template>
  <footer class="footer">
    <div class="container grid">
      <div class="about">
        <AppLogo light />
        <p>Home services, provider quotes, and job updates together in one place.</p>
        <div v-if="getConfiguredSocialLinks().length" class="social">
          <h3>Follow us</h3>
          <SocialLinks />
        </div>
      </div>

      <div>
        <h3>Services</h3>
        <ul>
          <li v-for="service in services" :key="service.slug">
            <NuxtLink :to="`/categories/${service.slug}`">{{ service.label }}</NuxtLink>
          </li>
        </ul>
      </div>

      <div>
        <h3>Company</h3>
        <ul>
          <li><NuxtLink to="/about">About us</NuxtLink></li>
          <li><NuxtLink to="/contact">Contact</NuxtLink></li>
          <li><NuxtLink to="/providers/browse">Find a provider</NuxtLink></li>
        </ul>
      </div>

      <div>
        <h3>Account</h3>
        <ul>
          <li><NuxtLink to="/auth/login">Sign in</NuxtLink></li>
          <li><NuxtLink to="/auth/register">Create account</NuxtLink></li>
          <li><NuxtLink to="/contact">Contact our team</NuxtLink></li>
        </ul>
      </div>
    </div>

    <div class="container legal">
      <p>© {{ year }} {{ config.siteName }}. All rights reserved.</p>
    </div>
  </footer>
</template>

<style scoped>
.footer { margin-top: 40px; padding: 52px 0 20px; color: #cbd5e1; background: var(--color-dark); }
.grid { display: grid; grid-template-columns: 2fr 1fr 1fr 1fr; gap: 32px; }
.about p { max-width: 320px; margin-top: 14px; color: #94a3b8; }
.social { margin-top: 24px; }
h3 { margin: 0 0 12px; font-size: 14px; letter-spacing: 0.06em; text-transform: uppercase; color: #fff; }
ul { padding: 0; margin: 0; list-style: none; display: grid; gap: 8px; }
a { color: #cbd5e1; text-decoration: none; }
a:hover { color: #fff; text-decoration: underline; }
.legal { margin-top: 32px; padding-top: 18px; border-top: 1px solid rgb(255 255 255 / 14%); font-size: 14px; color: #94a3b8; }
.legal p { margin: 0; }
@media (max-width: 760px) { .grid { grid-template-columns: 1fr 1fr; } .about { grid-column: 1 / -1; } }
</style>

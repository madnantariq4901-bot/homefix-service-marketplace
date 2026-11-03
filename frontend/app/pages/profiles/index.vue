<script setup lang="ts">
import { apiErrorMessage } from "~/services/api"

definePageMeta({
  middleware: "auth",
})

const userStore = useUserStore()
const authStore = useAuthStore()
const fullName = ref("")
const phone = ref("")
const error = ref("")
const message = ref("")
const saving = ref(false)

onMounted(async () => {
  try {
    const user = await userStore.fetchMyProfile()
    fullName.value = user.full_name
    phone.value = user.phone ?? ""
  } catch {
    // The store exposes the request error to the page.
  }
})

async function saveProfile() {
  error.value = ""
  message.value = ""
  saving.value = true
  try {
    const user = await authStore.updateProfile({
      full_name: fullName.value.trim(),
      phone: phone.value.trim() || null,
    })
    userStore.user = user
    message.value = "Your profile has been updated."
  } catch (err: unknown) {
    error.value = apiErrorMessage(err, "Unable to update your profile.")
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <main class="profile-page">
    <section class="profile-hero">
      <div>
        <p class="eyebrow">Your HomeFix account</p>
        <h1>Profile and account details.</h1>
        <p>Keep your contact information up to date so your account is ready when you need a service.</p>
      </div>
      <img src="https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?auto=format&fit=crop&w=1100&q=85" alt="A comfortable home" />
    </section>

    <AppLoader v-if="userStore.loading" />
    <AppAlert v-else-if="userStore.error" type="error">{{ userStore.error }}</AppAlert>
    <section v-else-if="userStore.user" class="profile-card">
      <div class="profile-heading">
        <span class="avatar" aria-hidden="true">{{ userStore.user.full_name.trim().slice(0, 1).toUpperCase() }}</span>
        <div><p class="eyebrow section-eyebrow">Account profile</p><h2>{{ userStore.user.full_name }}</h2><span class="role">{{ userStore.user.role }}</span></div>
      </div>
      <AppAlert v-if="error" type="error">{{ error }}</AppAlert>
      <AppAlert v-if="message" type="success">{{ message }}</AppAlert>
      <form class="profile-form" @submit.prevent="saveProfile">
        <label>
          Full name
          <input v-model="fullName" type="text" minlength="2" maxlength="120" autocomplete="name" required />
        </label>
        <label>
          Email address
          <input :value="userStore.user.email" type="email" disabled />
          <small>Email changes are not available yet.</small>
        </label>
        <label>
          Phone number
          <input v-model="phone" type="tel" maxlength="40" autocomplete="tel" />
        </label>
        <label>
          Account type
          <input :value="userStore.user.role" type="text" disabled />
        </label>
        <button type="submit" :disabled="saving || authStore.loading">
          {{ saving ? "Saving..." : "Save changes" }}
        </button>
      </form>
      <div class="profile-tip">
        <span aria-hidden="true">ℹ</span>
        <p>You can update your name and phone here. Email changes are not available yet; contact support if you need help.</p>
        <NuxtLink to="/contact">Contact support →</NuxtLink>
      </div>
    </section>
    <div v-else class="empty-profile">
      <h2>Profile unavailable</h2>
      <p>We could not find account details for this user.</p>
    </div>
  </main>
</template>

<style scoped>
.profile-page { max-width: 1100px; margin: 0 auto; padding: 28px; }
.profile-hero { display: grid; grid-template-columns: 1fr .8fr; align-items: center; gap: 32px; overflow: hidden; margin-bottom: 30px; padding: clamp(24px, 4vw, 38px); color: #fff; background: var(--color-dark); border-radius: 18px; }
.profile-hero h1 { margin: 0 0 12px; color: #fff; font-size: clamp(34px, 4vw, 48px); line-height: 1.08; }
.profile-hero p:not(.eyebrow) { max-width: 500px; color: #dbe5f2; }
.profile-hero img { width: 100%; height: 210px; object-fit: cover; border-radius: 14px; }
.eyebrow { margin: 0 0 9px; color: #ffc48d; font-size: 12px; font-weight: 700; letter-spacing: .15em; text-transform: uppercase; }
.profile-card { padding: 28px; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-lg); }
.profile-heading { display: flex; align-items: center; gap: 16px; padding-bottom: 22px; border-bottom: 1px solid var(--color-border); }
.avatar { display: grid; place-items: center; flex: 0 0 58px; width: 58px; height: 58px; color: #fff; background: var(--color-primary); border-radius: 18px; font-size: 25px; font-weight: 700; }
.section-eyebrow { margin-bottom: 4px; color: var(--color-primary); }
.profile-heading h2 { margin: 0; font-size: 24px; }
.role { display: inline-block; margin-top: 6px; padding: 3px 9px; color: var(--color-primary); background: var(--color-primary-soft); border-radius: 999px; font-size: 12px; font-weight: 700; text-transform: capitalize; }
.details { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0 28px; margin: 8px 0 22px; }
.details div { padding: 16px 0; border-bottom: 1px solid var(--color-border); }
.details dt { margin-bottom: 4px; color: var(--color-muted); font-size: 13px; }
.details dd { margin: 0; font-weight: 600; overflow-wrap: anywhere; }
.profile-form { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; margin: 22px 0; }
.profile-form label { display: grid; gap: 7px; font-size: 14px; font-weight: 600; }
.profile-form small { color: var(--color-muted); font-size: 12px; font-weight: 400; }
.profile-form button { justify-self: start; }
.profile-tip { display: flex; align-items: center; gap: 12px; padding: 15px; background: var(--color-page); border-radius: var(--radius); }
.profile-tip > span { color: var(--color-primary); font-size: 19px; }
.profile-tip p { flex: 1; margin: 0; color: var(--color-muted); font-size: 13px; }
.profile-tip a { color: var(--color-primary); font-size: 13px; font-weight: 700; text-decoration: none; white-space: nowrap; }
.empty-profile { padding: 26px; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-lg); }
.empty-profile p { color: var(--color-muted); }
@media (max-width: 740px) { .profile-page { padding: 18px; } .profile-hero { grid-template-columns: 1fr; } .profile-hero img { height: 190px; } .profile-tip { align-items: flex-start; flex-wrap: wrap; } .details, .profile-form { grid-template-columns: 1fr; } }
</style>
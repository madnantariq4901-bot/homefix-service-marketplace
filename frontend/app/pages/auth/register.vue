<script setup lang="ts">
import { apiErrorMessage } from "~/services/api"
import { getSafeRedirectPath } from "~/utils/authRedirect"

definePageMeta({ middleware: "guest" })

const route = useRoute()
const authStore = useAuthStore()
const fullName = ref("")
const email = ref("")
const phone = ref("")
const password = ref("")
const role = ref<"customer" | "provider">(route.query.role === "provider" ? "provider" : "customer")
const redirectPath = getSafeRedirectPath(route.query.redirect)
const error = ref("")
const showPassword = ref(false)

async function submit() {
  error.value = ""
  try {
    await authStore.register({
      email: email.value.trim(),
      password: password.value,
      full_name: fullName.value.trim(),
      ...(phone.value.trim() ? { phone: phone.value.trim() } : {}),
      role: role.value,
    })
    await navigateTo({
      path: "/auth/login",
      query: {
        registered: "1",
        role: role.value,
        ...(redirectPath ? { redirect: redirectPath } : {}),
      },
    })
  } catch (err: unknown) {
    error.value = apiErrorMessage(err, "Registration failed. Check your details and try again.")
  }
}
</script>

<template>
  <main class="auth-page">
    <section class="auth-card">
      <h1>Create account</h1>
      <form @submit.prevent="submit">
        <label>
          Full name
          <input v-model="fullName" type="text" autocomplete="name" minlength="2" maxlength="120" required />
        </label>
        <label>
          Email
          <input v-model="email" type="email" autocomplete="email" required />
        </label>
        <label>
          Phone (optional)
          <input v-model="phone" type="tel" autocomplete="tel" maxlength="40" />
        </label>
        <label>
          Account type
          <select v-model="role">
            <option value="customer">Customer</option>
            <option value="provider">Service provider</option>
          </select>
        </label>
        <p v-if="role === 'provider'" class="hint">
          After signing in, add a matching skill, set your availability, and submit your ID images and live selfie before quoting. The blue badge is earned after 5 completed jobs; uploaded ID images are not automatically authenticated.
        </p>
        <label>
          Password
          <span class="password-field">
            <input v-model="password" :type="showPassword ? 'text' : 'password'" autocomplete="new-password" minlength="8" maxlength="72" required />
            <button type="button" class="toggle" :aria-label="showPassword ? 'Hide password' : 'Show password'" @click="showPassword = !showPassword">
              {{ showPassword ? "Hide" : "Show" }}
            </button>
          </span>
          <small class="hint">At least 8 characters.</small>
        </label>
        <AppAlert v-if="error" type="error">{{ error }}</AppAlert>
        <button type="submit" :disabled="authStore.loading">
          {{ authStore.loading ? "Creating account..." : "Create account" }}
        </button>
      </form>
      <p>Already registered? <NuxtLink to="/auth/login">Sign in</NuxtLink></p>
    </section>
  </main>
</template>

<style scoped>
.auth-page { min-height: 80vh; display: grid; place-items: center; padding: 28px 16px; }
.auth-card { width: min(440px, 100%); padding: 28px; border: 1px solid var(--color-border); border-radius: 10px; background: var(--color-surface); }
h1 { margin-top: 0; }
form, label { display: flex; flex-direction: column; gap: 8px; }
form { gap: 16px; margin: 22px 0; }
label { color: var(--color-text); font-size: 14px; font-weight: 600; }
.auth-card p { color: var(--color-muted); }
.auth-card a { color: var(--color-text); }
.password-field { position: relative; display: block; }
.password-field input { width: 100%; padding-right: 70px; }
.password-field .toggle { position: absolute; top: 50%; right: 8px; min-height: 0; padding: 4px 8px; color: var(--color-primary); background: transparent; border: 0; box-shadow: none; transform: translateY(-50%); font-size: 13px; font-weight: 700; }
.password-field .toggle:hover:not(:disabled) { background: var(--color-primary-soft); box-shadow: none; transform: translateY(-50%); }
.hint { margin: 0; color: var(--color-muted); font-size: 13px; font-weight: 400; }
</style>

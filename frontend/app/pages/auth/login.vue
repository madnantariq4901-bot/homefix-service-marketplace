<script setup lang="ts">
import { apiErrorMessage } from "~/services/api"
import { getSafeRedirectPath } from "~/utils/authRedirect"

definePageMeta({ middleware: "guest" })

const auth = useAuthStore()
const route = useRoute()
const registered = computed(() => route.query.registered === "1")
const redirectPath = computed(() => getSafeRedirectPath(route.query.redirect))
const registrationTarget = computed(() => ({
  path: "/auth/register",
  query: {
    ...(redirectPath.value ? { redirect: redirectPath.value } : {}),
    ...(route.query.role === "provider" || redirectPath.value?.startsWith("/providers") ? { role: "provider" } : {}),
  },
}))
const email = ref("")
const password = ref("")
const error = ref("")
const showPassword = ref(false)

async function handleLogin() {
  error.value = ""
  try {
    await auth.login(email.value.trim(), password.value)
    await navigateTo(redirectPath.value ?? "/dashboard")
  } catch (err: unknown) {
    error.value = apiErrorMessage(err, "Login failed. Check your email and password.")
  }
}
</script>

<template>
  <main class="auth-page">
    <section class="auth-card">
      <h1>Sign in</h1>
      <AppAlert v-if="registered" type="success">Account created. You can now sign in.</AppAlert>
      <form @submit.prevent="handleLogin">
        <label>
          Email
          <input v-model="email" type="email" autocomplete="email" required />
        </label>
        <label>
          Password
          <span class="password-field">
            <input v-model="password" :type="showPassword ? 'text' : 'password'" autocomplete="current-password" required />
            <button type="button" class="toggle" :aria-label="showPassword ? 'Hide password' : 'Show password'" @click="showPassword = !showPassword">
              {{ showPassword ? "Hide" : "Show" }}
            </button>
          </span>
        </label>
        <AppAlert v-if="error" type="error">{{ error }}</AppAlert>
        <button type="submit" :disabled="auth.loading">
          {{ auth.loading ? "Signing in..." : "Sign in" }}
        </button>
      </form>
      <p class="forgot-password"><NuxtLink to="/auth/forgot-password">Forgot password?</NuxtLink></p>
      <p>Don't have an account? <NuxtLink :to="registrationTarget">Create one</NuxtLink></p>
    </section>
  </main>
</template>

<style scoped>
.auth-page { min-height: 80vh; display: grid; place-items: center; padding: 28px 16px; }
.auth-card { width: min(400px, 100%); padding: 28px; border: 1px solid var(--color-border); border-radius: 10px; background: var(--color-surface); }
h1 { margin-top: 0; }
form, label { display: flex; flex-direction: column; gap: 8px; }
form { gap: 16px; margin: 22px 0; }
label { font-size: 14px; font-weight: 600; }
.auth-card p { color: var(--color-muted); }
.forgot-password { margin-top: -12px; }
.password-field { position: relative; display: block; }
.password-field input { width: 100%; padding-right: 70px; }
.password-field .toggle { position: absolute; top: 50%; right: 8px; min-height: 0; padding: 4px 8px; color: var(--color-primary); background: transparent; border: 0; box-shadow: none; transform: translateY(-50%); font-size: 13px; font-weight: 700; }
.password-field .toggle:hover:not(:disabled) { background: var(--color-primary-soft); box-shadow: none; transform: translateY(-50%); }
.hint { margin: 0; color: var(--color-muted); font-size: 13px; font-weight: 400; }
</style>

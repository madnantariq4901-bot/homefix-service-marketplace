<script setup lang="ts">
import { apiErrorMessage } from "~/services/api"
import { authService } from "~/services/auth.service"

definePageMeta({ middleware: "guest" })

const email = ref("")
const error = ref("")
const submitted = ref(false)
const loading = ref(false)

async function requestReset() {
  error.value = ""
  loading.value = true
  try {
    await authService.requestPasswordReset(email.value.trim())
    submitted.value = true
  } catch (err: unknown) {
    error.value = apiErrorMessage(err, "Could not request a password reset. Please try again.")
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <main class="auth-page">
    <section class="auth-card">
      <h1>Forgot password?</h1>
      <template v-if="submitted">
        <AppAlert type="success">If an account exists for this email, a password reset link has been sent.</AppAlert>
        <NuxtLink to="/auth/login">Back to sign in</NuxtLink>
      </template>
      <template v-else>
        <p>Enter your account email and we’ll send you a link to reset your password.</p>
        <form @submit.prevent="requestReset">
          <label>
            Email
            <input v-model="email" type="email" autocomplete="email" required />
          </label>
          <AppAlert v-if="error" type="error">{{ error }}</AppAlert>
          <button type="submit" :disabled="loading">
            {{ loading ? "Sending..." : "Send reset link" }}
          </button>
        </form>
        <NuxtLink to="/auth/login">Back to sign in</NuxtLink>
      </template>
    </section>
  </main>
</template>

<style scoped>
.auth-page { min-height: 80vh; display: grid; place-items: center; padding: 28px 16px; }
.auth-card { width: min(440px, 100%); padding: 28px; border: 1px solid var(--color-border); border-radius: 10px; background: var(--color-surface); }
h1 { margin-top: 0; }
p { color: var(--color-muted); }
form, label { display: flex; flex-direction: column; gap: 8px; }
form { gap: 16px; margin: 22px 0; }
label { font-size: 14px; font-weight: 600; }
</style>

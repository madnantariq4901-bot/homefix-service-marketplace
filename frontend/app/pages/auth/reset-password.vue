<script setup lang="ts">
import { apiErrorMessage } from "~/services/api"
import { authService } from "~/services/auth.service"

definePageMeta({ middleware: "guest" })

const route = useRoute()
const token = computed(() => typeof route.query.token === "string" ? route.query.token : "")
const password = ref("")
const confirmPassword = ref("")
const error = ref("")
const complete = ref(false)
const loading = ref(false)

async function resetPassword() {
  error.value = ""
  if (!token.value) {
    error.value = "This password reset link is invalid or expired."
    return
  }
  if (password.value !== confirmPassword.value) {
    error.value = "Passwords do not match."
    return
  }

  loading.value = true
  try {
    await authService.resetPassword(token.value, password.value)
    complete.value = true
  } catch (err: unknown) {
    error.value = apiErrorMessage(err, "Could not reset your password. The link may have expired.")
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <main class="auth-page">
    <section class="auth-card">
      <h1>Reset password</h1>
      <template v-if="complete">
        <AppAlert type="success">Your password has been updated. You can now sign in.</AppAlert>
        <NuxtLink to="/auth/login">Back to sign in</NuxtLink>
      </template>
      <template v-else>
        <form @submit.prevent="resetPassword">
          <label>
            New password
            <input v-model="password" type="password" autocomplete="new-password" minlength="8" maxlength="72" required />
          </label>
          <label>
            Confirm new password
            <input v-model="confirmPassword" type="password" autocomplete="new-password" minlength="8" maxlength="72" required />
          </label>
          <AppAlert v-if="error" type="error">{{ error }}</AppAlert>
          <button type="submit" :disabled="loading">
            {{ loading ? "Updating..." : "Update password" }}
          </button>
        </form>
      </template>
    </section>
  </main>
</template>

<style scoped>
.auth-page { min-height: 80vh; display: grid; place-items: center; padding: 28px 16px; }
.auth-card { width: min(440px, 100%); padding: 28px; border: 1px solid var(--color-border); border-radius: 10px; background: var(--color-surface); }
h1 { margin-top: 0; }
form, label { display: flex; flex-direction: column; gap: 8px; }
form { gap: 16px; margin: 22px 0; }
label { font-size: 14px; font-weight: 600; }
</style>

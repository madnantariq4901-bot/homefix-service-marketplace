<script setup lang="ts">
import type { ProviderAdminDirectoryItem } from "~/types/provider"
import { providersService } from "~/services/provider.service"

definePageMeta({ middleware: ["auth", "role"], requiredRole: "admin" })

const authStore = useAuthStore()
const providers = ref<ProviderAdminDirectoryItem[]>([])
const error = ref("")
const message = ref("")
const loading = ref(false)

async function loadProviders() {
  loading.value = true
  error.value = ""
  try {
    const user = authStore.user || await authStore.loadCurrentUser()
    if (user?.role !== "admin") { error.value = "This page is only available to administrators."; return }
    providers.value = await providersService.getProviders()
  } catch (err: any) {
    error.value = err?.data?.detail || "Unable to load providers."
  } finally {
    loading.value = false
  }
}

async function setVerification(providerId: number, isVerified: boolean) {
  error.value = ""
  message.value = ""
  try {
    await providersService.updateVerification(providerId, isVerified)
    const provider = providers.value.find(item => item.id === providerId)
    if (provider) provider.is_verified = isVerified
    message.value = "Provider marketplace badge updated."
  } catch (err: any) {
    error.value = err?.data?.detail || "Unable to update provider verification."
  }
}

onMounted(loadProviders)
</script>

<template>
  <main class="admin-page">
    <h1>Provider marketplace badges</h1>
    <AppAlert v-if="error" type="error">{{ error }}</AppAlert>
    <AppAlert v-if="message" type="success">{{ message }}</AppAlert>
    <AppLoader v-if="loading" />
    <p v-else-if="!providers.length">No providers found.</p>
    <div v-else class="provider-list">
      <article v-for="provider in providers" :key="provider.id" class="provider-card">
        <div>
          <h2>{{ provider.full_name }}</h2>
          <p>Provider #{{ provider.id }} · Account #{{ provider.user_id }}</p>
          <p>Skills: {{ provider.skills.map(skill => `#${skill.category_id}`).join(", ") || "None" }}</p>
          <p>Completed jobs: {{ provider.completed_job_count }} · ID documents submitted: {{ provider.identity_documents_submitted ? "Yes" : "No" }}</p>
          <p>Availability: {{ provider.is_available ? "Available" : "Unavailable" }}</p>
        </div>
        <button type="button" @click="setVerification(provider.id, !provider.is_verified)">
          {{ provider.is_verified ? "Remove marketplace badge" : "Set marketplace badge" }}
        </button>
      </article>
    </div>
  </main>
</template>

<style scoped>
.admin-page { max-width: 1000px; margin: 0 auto; padding: 28px 16px; }
.provider-list { display: grid; gap: 14px; margin-top: 20px; }
.provider-card { display: flex; justify-content: space-between; align-items: center; gap: 20px; padding: 18px; border: 1px solid var(--color-border); border-radius: 10px; background: var(--color-surface); }
h2 { margin: 0 0 6px; font-size: 18px; }
p { margin: 4px 0; color: var(--color-muted); }
button { flex-shrink: 0; }
@media (max-width: 600px) { .provider-card { align-items: flex-start; flex-direction: column; } }
</style>

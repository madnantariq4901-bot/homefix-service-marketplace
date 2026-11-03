<script setup lang="ts">
definePageMeta({ middleware: ["auth", "role"], requiredRole: "provider" })

const authStore = useAuthStore()
const providersStore = useProvidersStore()
const categoriesStore = useCategoriesStore()
const categoryId = ref<number | null>(null)
const yearsExperience = ref(0)
const pickedLat = ref<number | null>(null)
const pickedLng = ref<number | null>(null)
const pickedAddress = ref("")
const pageError = ref("")
const pageMessage = ref("")

onMounted(async () => {
  try {
    const user = authStore.user || await authStore.loadCurrentUser()
    if (user?.role === "provider") {
      await Promise.all([providersStore.fetchMyProfile(), categoriesStore.fetchCategories()])
      if (categoriesStore.categories.length) categoryId.value = categoriesStore.categories[0].id
    }
  } catch (err: any) {
    pageError.value = err?.data?.detail || providersStore.error || categoriesStore.error || "Unable to load provider profile."
  }
})

function onPicked(p: { address: string; city: string; latitude: number; longitude: number }) {
  pickedAddress.value = p.address
  pickedLat.value = p.latitude
  pickedLng.value = p.longitude
}

function onLocationCleared() {
  pickedLat.value = null
  pickedLng.value = null
}

async function addSkill() {
  pageError.value = ""
  pageMessage.value = ""
  if (!categoryId.value) { pageError.value = "Choose a service category."; return }
  try {
    await providersStore.addSkill({ category_id: categoryId.value, years_experience: yearsExperience.value })
    await providersStore.fetchMyProfile()
    pageMessage.value = "Skill saved."
  } catch (err: any) {
    pageError.value = err?.data?.detail || providersStore.error || "Unable to save skill."
  }
}

async function setAvailability(event: Event) {
  const input = event.target as HTMLInputElement
  pageError.value = ""
  pageMessage.value = ""
  try {
    await providersStore.updateAvailability(input.checked)
    pageMessage.value = "Availability updated."
  } catch (err: any) {
    input.checked = !input.checked
    pageError.value = err?.data?.detail || providersStore.error || "Unable to update availability."
  }
}

async function saveLocation() {
  pageError.value = ""
  pageMessage.value = ""
  if (pickedLat.value === null || pickedLng.value === null) {
    pageError.value = "Choose your work location on the map first."
    return
  }
  try {
    await providersStore.updateLocation({ lat: pickedLat.value, lng: pickedLng.value })
    await providersStore.fetchMyProfile()
    pageMessage.value = "Location saved."
  } catch (err: any) {
    pageError.value = err?.data?.detail || providersStore.error || "Unable to save location."
  }
}
</script>

<template>
  <main class="providers-page">
    <section class="provider-hero">
      <div>
        <p class="eyebrow">Build your professional presence</p>
        <h1>Provider profile</h1>
        <p>Share your skills, work location, and availability so customers can find the right professional for their jobs.</p>
      </div>
      <img src="https://images.unsplash.com/photo-1621905251918-48416bd8575a?auto=format&fit=crop&w=1000&q=85" alt="A professional working on a home service" />
    </section>
    <AppLoader v-if="providersStore.loading && !providersStore.provider" />
    <AppAlert v-else-if="authStore.user?.role !== 'provider'" type="info">This page is available to service-provider accounts.</AppAlert>
    <template v-else-if="providersStore.provider">
      <AppAlert v-if="pageError || providersStore.error || categoriesStore.error" type="error">{{ pageError || providersStore.error || categoriesStore.error }}</AppAlert>
      <AppAlert v-if="pageMessage" type="success">{{ pageMessage }}</AppAlert>
      <section class="profile-card">
        <div class="profile-heading">
          <h2>{{ authStore.user.full_name }}</h2>
          <span v-if="providersStore.provider.is_verified" class="verified-badge" title="Marketplace verified badge">✓</span>
        </div>
        <p>Rating: {{ providersStore.provider.rating_avg.toFixed(1) }} ({{ providersStore.provider.rating_count }} reviews)</p>
        <p>{{ providersStore.provider.is_verified ? "Your profile currently has the marketplace verified badge." : `Complete ${Math.max(0, 5 - providersStore.provider.completed_job_count)} more jobs to earn the verified badge.` }}</p>
        <p>Completed jobs: <strong>{{ providersStore.provider.completed_job_count }}</strong> / 5</p>
        <label class="availability">
          <input type="checkbox" :checked="providersStore.provider.is_available" :disabled="providersStore.loading" @change="setAvailability"/>
          Available for new jobs
        </label>
      </section>
      <section class="form-card">
        <h2>Identity documents</h2>
        <AppAlert v-if="providersStore.provider.identity_documents_submitted" type="success">
          ID images and live selfie submitted. You can quote when your matching skill is saved and you are available. The upload is not an automatic government-ID authenticity check.
        </AppAlert>
        <ProviderIdentityForm v-else />
      </section>
      <section class="form-card">
        <h2>Service skills</h2>
        <form @submit.prevent="addSkill">
          <label>Service category
            <select v-model.number="categoryId" required>
              <option v-for="category in categoriesStore.categories" :key="category.id" :value="category.id">{{ category.name }}</option>
            </select>
          </label>
          <label>Years of experience
            <input v-model.number="yearsExperience" type="number" min="0" max="80" required />
          </label>
          <button type="submit" :disabled="providersStore.loading || !categoriesStore.categories.length">Save skill</button>
        </form>
        <p v-if="!providersStore.provider.skills.length">No skills added yet.</p>
        <ul v-else>
          <li v-for="skill in providersStore.provider.skills" :key="skill.id">{{ categoriesStore.categories.find(item => item.id === skill.category_id)?.name || `Category #${skill.category_id}` }} — {{ skill.years_experience }} years</li>
        </ul>
      </section>
      <section class="form-card">
        <h2>Work location</h2>
        <p v-if="providersStore.provider.current_lat != null" class="help-text">
          A location is already saved for your profile. Pick a new one below to replace it.
        </p>
        <p v-else class="help-text">Search your work address or click the map, then save.</p>
        <ClientOnly>
          <AddressMapPicker @picked="onPicked" @cleared="onLocationCleared" />
        </ClientOnly>
        <form class="location-form" @submit.prevent="saveLocation">
          <p v-if="pickedAddress" class="help-text">Selected: {{ pickedAddress }}</p>
          <button type="submit" :disabled="providersStore.loading || pickedLat === null">Save location</button>
        </form>
      </section>
    </template>
  </main>
</template>

<style scoped>
.providers-page { max-width: 900px; margin: 0 auto; padding: 28px 16px; }
.provider-hero { display: grid; grid-template-columns: 1fr .8fr; align-items: center; gap: 24px; overflow: hidden; margin-bottom: 24px; padding: 24px; color: #fff; background: var(--color-dark); border-radius: 16px; }
.provider-hero h1 { margin: 0 0 8px; color: #fff; font-size: clamp(30px, 4vw, 40px); }
.provider-hero p:not(.eyebrow) { margin: 0; color: #dbe5f2; }
.provider-hero img { width: 100%; height: 170px; object-fit: cover; border-radius: 12px; }
.eyebrow { margin: 0 0 8px; color: #ffc48d; font-size: 11px; font-weight: 700; letter-spacing: .14em; text-transform: uppercase; }
.profile-card, .form-card { margin: 18px 0; padding: 22px; border: 1px solid var(--color-border); border-radius: 10px; background: var(--color-surface); }
.profile-heading { display: flex; align-items: center; justify-content: space-between; gap: 18px; }
.profile-heading h2 { margin: 0; }
.profile-heading span { font-size: 14px; }
.verified-badge { display: inline-grid; place-items: center; width: 22px; height: 22px; color: #fff; background: #1687f8; border-radius: 50%; font-size: 14px; font-weight: 800; }
form, label { display: flex; flex-direction: column; gap: 8px; }
form { gap: 14px; max-width: 520px; }
.location-form { margin-top: 14px; max-width: none; }
label { font-size: 14px; font-weight: 600; }
.availability { flex-direction: row; align-items: center; margin-top: 16px; }
.availability input { width: auto; }
.help-text { color: var(--color-muted); }
button { width: fit-content; }
@media (max-width: 650px) { .provider-hero { grid-template-columns: 1fr; } .provider-hero img { height: 200px; } }
</style>
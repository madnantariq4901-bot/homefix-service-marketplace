<script setup lang="ts">
import { categoriesService } from "~/services/categories.service"
import type { Category } from "~/types/category"

definePageMeta({ middleware: ["auth", "role"], requiredRole: "admin" })
useHead({ title: "Manage services" })

const categories = ref<Category[]>([])
const loading = ref(false)
const saving = ref(false)
const error = ref("")
const message = ref("")
const editingId = ref<number | null>(null)
const newService = reactive<{ name: string; base_hourly_rate: number | null; description: string }>({
  name: "",
  base_hourly_rate: null,
  description: "",
})
const editDraft = reactive<{ name: string; base_hourly_rate: number | null; description: string }>({
  name: "",
  base_hourly_rate: null,
  description: "",
})

function labelFor(name: string) {
  return name.replaceAll("_", " ").replace(/\b\w/g, character => character.toUpperCase())
}

async function loadCategories() {
  loading.value = true
  error.value = ""
  try {
    categories.value = await categoriesService.getCategories()
  } catch (err: any) {
    error.value = err?.data?.detail || "Unable to load services."
  } finally {
    loading.value = false
  }
}

async function addService() {
  if (!newService.name.trim() || newService.base_hourly_rate === null) return
  saving.value = true
  error.value = ""
  message.value = ""
  try {
    const category = await categoriesService.createCategory({
      name: newService.name.trim(),
      base_hourly_rate: newService.base_hourly_rate,
      description: newService.description.trim() || undefined,
    })
    categories.value.push(category)
    newService.name = ""
    newService.base_hourly_rate = null
    newService.description = ""
    message.value = "Service added."
  } catch (err: any) {
    error.value = err?.data?.detail || "Unable to add service."
  } finally {
    saving.value = false
  }
}

function beginEdit(category: Category) {
  editingId.value = category.id
  editDraft.name = category.name
  editDraft.base_hourly_rate = category.base_hourly_rate
  editDraft.description = category.description || ""
  error.value = ""
  message.value = ""
}

async function saveEdit() {
  if (editingId.value === null || !editDraft.name.trim() || editDraft.base_hourly_rate === null) return
  saving.value = true
  error.value = ""
  message.value = ""
  try {
    const updated = await categoriesService.updateCategory(editingId.value, {
      name: editDraft.name.trim(),
      base_hourly_rate: editDraft.base_hourly_rate,
      description: editDraft.description.trim() || null,
    })
    categories.value = categories.value.map(category => category.id === updated.id ? updated : category)
    editingId.value = null
    message.value = "Service updated."
  } catch (err: any) {
    error.value = err?.data?.detail || "Unable to update service."
  } finally {
    saving.value = false
  }
}

async function removeService(category: Category) {
  if (!window.confirm(`Remove ${labelFor(category.name)} from the service marketplace?`)) return
  error.value = ""
  message.value = ""
  try {
    await categoriesService.deleteCategory(category.id)
    categories.value = categories.value.filter(item => item.id !== category.id)
    message.value = "Service removed."
  } catch (err: any) {
    error.value = err?.data?.detail || "Unable to remove service."
  }
}

onMounted(loadCategories)
</script>

<template>
  <main class="admin-page">
    <header class="page-heading">
      <div>
        <p class="eyebrow">Marketplace administration</p>
        <h1>Services</h1>
        <p class="muted">Manage service names, descriptions, and base hourly rates.</p>
      </div>
      <NuxtLink class="btn btn-outline" to="/jobs">Manage jobs</NuxtLink>
    </header>

    <AppAlert v-if="error" type="error">{{ error }}</AppAlert>
    <AppAlert v-if="message" type="success">{{ message }}</AppAlert>

    <form class="add-form" @submit.prevent="addService">
      <h2>Add a service</h2>
      <div class="form-grid">
        <label>Service name
          <input v-model="newService.name" maxlength="80" minlength="2" placeholder="e.g. Window cleaning" required />
        </label>
        <label>Base hourly rate
          <input v-model.number="newService.base_hourly_rate" type="number" min="0.01" max="1000000" step="0.01" required />
        </label>
        <label class="description-field">Description
          <textarea v-model="newService.description" maxlength="1000" rows="2" />
        </label>
      </div>
      <button class="btn btn-primary" type="submit" :disabled="saving">
        {{ saving ? "Saving..." : "Add service" }}
      </button>
    </form>

    <section class="service-section">
      <div class="section-heading">
        <h2>Marketplace services</h2>
        <span>{{ categories.length }} {{ categories.length === 1 ? "service" : "services" }}</span>
      </div>
      <AppLoader v-if="loading" />
      <p v-else-if="!categories.length" class="empty-state">No services have been added.</p>
      <div v-else class="service-list">
        <article v-for="category in categories" :key="category.id" class="service-row">
          <form v-if="editingId === category.id" class="service-edit" @submit.prevent="saveEdit">
            <div class="form-grid">
              <label>Service name
                <input v-model="editDraft.name" maxlength="80" minlength="2" required />
              </label>
              <label>Base hourly rate
                <input v-model.number="editDraft.base_hourly_rate" type="number" min="0.01" max="1000000" step="0.01" required />
              </label>
              <label class="description-field">Description
                <textarea v-model="editDraft.description" maxlength="1000" rows="2" />
              </label>
            </div>
            <div class="row-actions">
              <button class="btn btn-primary" type="submit" :disabled="saving">{{ saving ? "Saving..." : "Save changes" }}</button>
              <button class="btn btn-outline" type="button" @click="editingId = null">Cancel</button>
            </div>
          </form>
          <template v-else>
            <div class="service-info">
              <div class="service-title"><h3>{{ labelFor(category.name) }}</h3><span>{{ category.base_hourly_rate.toLocaleString() }} / hour</span></div>
              <p>{{ category.description || "No description" }}</p>
            </div>
            <div class="row-actions">
              <button class="btn btn-outline" type="button" @click="beginEdit(category)">Edit</button>
              <button class="btn btn-danger" type="button" @click="removeService(category)">Remove</button>
            </div>
          </template>
        </article>
      </div>
    </section>
  </main>
</template>

<style scoped>
.admin-page { max-width: 1050px; margin: 0 auto; padding: 28px 16px 56px; }
.page-heading, .section-heading, .service-title, .row-actions { display: flex; align-items: center; justify-content: space-between; gap: 14px; }
.page-heading { margin-bottom: 24px; }
.page-heading h1 { margin: 0 0 5px; }
.eyebrow { margin: 0 0 6px; color: var(--color-primary); font-size: 12px; font-weight: 700; text-transform: uppercase; }
.muted, .service-info p { margin: 0; color: var(--color-muted); }
.add-form { display: grid; gap: 16px; padding: 20px; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: 8px; }
.add-form h2, .section-heading h2 { margin: 0; font-size: 20px; }
.form-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
label { display: grid; gap: 6px; font-size: 13px; font-weight: 700; }
input, select, textarea { width: 100%; }
.description-field { grid-column: 1 / -1; }
.service-section { margin-top: 32px; }
.section-heading { margin-bottom: 12px; }
.section-heading span { color: var(--color-muted); font-size: 13px; }
.service-list { border-top: 1px solid var(--color-border); }
.service-row { display: flex; align-items: center; justify-content: space-between; gap: 20px; padding: 17px 4px; border-bottom: 1px solid var(--color-border); }
.service-info { min-width: 0; }
.service-title { justify-content: flex-start; flex-wrap: wrap; }
.service-title h3 { margin: 0; font-size: 16px; }
.service-title span { color: var(--color-primary); font-size: 13px; font-weight: 700; }
.service-info p { margin-top: 5px; font-size: 13px; }
.service-edit { display: grid; flex: 1; gap: 14px; }
.row-actions { justify-content: flex-start; flex-shrink: 0; }
.btn-danger { color: #a32118; background: transparent; border-color: #e7b6b2; }
.btn-danger:hover:not(:disabled) { background: #fff1f0; }
.empty-state { padding: 24px 4px; color: var(--color-muted); }
@media (max-width: 680px) {
  .page-heading, .service-row { align-items: flex-start; flex-direction: column; }
  .form-grid { grid-template-columns: 1fr; }
  .description-field { grid-column: auto; }
}
</style>
import { defineStore } from "pinia"

import {
  providersService,
  type Provider,
  type SkillCreate,
  type LocationUpdate,
} from "~/services/provider.service"

export const useProvidersStore = defineStore("providers", () => {
  const provider = ref<Provider | null>(null)
  const loading = ref(false)
  const error = ref("")

  async function fetchMyProfile() {
    loading.value = true
    error.value = ""

    try {
      provider.value =
        await providersService.getMyProfile()

      return provider.value
    } catch (err: any) {
      error.value =
        err?.data?.detail ||
        "Unable to load provider profile."

      throw err
    } finally {
      loading.value = false
    }
  }

  async function addSkill(data: SkillCreate) {
    loading.value = true
    error.value = ""

    try {
      const skill =
        await providersService.addSkill(data)

      if (provider.value) {
        const index =
          provider.value.skills.findIndex(
            item =>
              item.category_id ===
              skill.category_id
          )

        if (index >= 0) {
          provider.value.skills[index] = skill
        } else {
          provider.value.skills.push(skill)
        }
      }

      return skill
    } catch (err: any) {
      error.value =
        err?.data?.detail ||
        "Unable to add skill."

      throw err
    } finally {
      loading.value = false
    }
  }

  async function uploadIdentityDocuments(data: FormData) {
    loading.value = true
    error.value = ""

    try {
      provider.value = await providersService.uploadIdentityDocuments(data)
      return provider.value
    } catch (err: any) {
      error.value = err?.data?.detail || "Unable to submit identity documents."
      throw err
    } finally {
      loading.value = false
    }
  }

  async function updateAvailability(
    isAvailable: boolean
  ) {
    loading.value = true
    error.value = ""

    try {
      provider.value =
        await providersService.updateAvailability({
          is_available: isAvailable,
        })

      return provider.value
    } catch (err: any) {
      error.value =
        err?.data?.detail ||
        "Unable to update availability."

      throw err
    } finally {
      loading.value = false
    }
  }

  async function updateLocation(
    data: LocationUpdate
  ) {
    loading.value = true
    error.value = ""

    try {
      provider.value =
        await providersService.updateLocation(data)

      return provider.value
    } catch (err: any) {
      error.value =
        err?.data?.detail ||
        "Unable to update location."

      throw err
    } finally {
      loading.value = false
    }
  }

  return {
    provider,
    loading,
    error,

    fetchMyProfile,
    addSkill,
    uploadIdentityDocuments,
    updateAvailability,
    updateLocation,
  }
})
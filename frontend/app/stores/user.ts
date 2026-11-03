import { defineStore } from "pinia"

import { usersService } from "~/services/users.service"
import type { User } from "~/types/user"

export const useUserStore = defineStore("user", () => {
  const user = ref<User | null>(null)
  const loading = ref(false)
  const error = ref("")

  async function fetchMyProfile() {
    loading.value = true
    error.value = ""
    try {
      user.value = await usersService.getMyProfile()
      return user.value
    } catch (err: any) {
      error.value = err?.data?.detail || "Unable to load profile."
      throw err
    } finally {
      loading.value = false
    }
  }

  return { user, loading, error, fetchMyProfile }
})

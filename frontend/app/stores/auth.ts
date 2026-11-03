import { defineStore } from "pinia"

import { authService, type RegisterData } from "~/services/auth.service"
import { usersService } from "~/services/users.service"
import type { User, UserUpdate } from "~/types/user"

export const useAuthStore = defineStore("auth", () => {
  const user = ref<User | null>(null)
  const userStore = useUserStore()
  const loading = ref(false)
  const token = useCookie<string | null>("access_token", { sameSite: "lax" })
  const isAuthenticated = computed(() => Boolean(token.value))

  async function login(email: string, password: string) {
    loading.value = true
    try {
      const response = await authService.login({ email, password })
      token.value = response.access_token
      user.value = await usersService.getMyProfile(response.access_token)
      userStore.user = user.value
      return user.value
    } catch (error) {
      token.value = null
      user.value = null
      userStore.user = null
      throw error
    } finally {
      loading.value = false
    }
  }

  async function register(data: RegisterData) {
    loading.value = true
    try {
      return await authService.register(data)
    } finally {
      loading.value = false
    }
  }

  async function updateProfile(data: UserUpdate) {
    loading.value = true
    try {
      user.value = await usersService.updateMyProfile(data)
      userStore.user = user.value
      return user.value
    } finally {
      loading.value = false
    }
  }

  async function loadCurrentUser() {
    if (!token.value) {
      user.value = null
      userStore.user = null
      return null
    }
    loading.value = true
    try {
      user.value = await usersService.getMyProfile()
      userStore.user = user.value
      return user.value
    } catch (error) {
      token.value = null 
      user.value = null
      userStore.user = null
      throw error
    } finally {
      loading.value = false
    }
  }

  async function logout() {
    token.value = null
    user.value = null
    userStore.user = null
    await navigateTo("/auth/login")
  }

  return { user, loading, token, isAuthenticated, login, register, updateProfile, loadCurrentUser, logout }
})

export default defineNuxtRouteMiddleware(async (to) => {
  const authStore = useAuthStore()
  if (!authStore.token) {
    return navigateTo({ path: "/auth/login", query: { redirect: to.fullPath } })
  }
  if (!authStore.user) {
    try {
      await authStore.loadCurrentUser()
    } catch {
      return navigateTo({ path: "/auth/login", query: { redirect: to.fullPath } })
    }
  }
})

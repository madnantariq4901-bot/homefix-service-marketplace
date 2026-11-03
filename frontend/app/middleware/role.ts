export default defineNuxtRouteMiddleware(async (to) => {
  const requiredRole = to.meta.requiredRole
  if (!requiredRole) return

  const authStore = useAuthStore()
  const requiredRoles = Array.isArray(requiredRole) ? requiredRole : [requiredRole]
  const loginQuery = {
    redirect: to.fullPath,
    ...(requiredRoles.includes("provider") ? { role: "provider" } : {}),
  }
  if (!authStore.token) return navigateTo({ path: "/auth/login", query: loginQuery })

  try {
    const user = authStore.user || await authStore.loadCurrentUser()
    const allowed = Array.isArray(requiredRole) ? requiredRole : [requiredRole]
    if (!user || !allowed.includes(user.role)) return navigateTo("/dashboard")
  } catch {
    return navigateTo({ path: "/auth/login", query: loginQuery })
  }
})

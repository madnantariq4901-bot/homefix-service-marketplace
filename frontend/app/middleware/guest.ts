import { getSafeRedirectPath } from "~/utils/authRedirect"

export default defineNuxtRouteMiddleware((to) => {
  const token = useCookie<string | null>("access_token")
  if (token.value) {
    return navigateTo(getSafeRedirectPath(to.query.redirect) ?? "/dashboard")
  }
})

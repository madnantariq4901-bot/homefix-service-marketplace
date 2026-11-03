export function useAuth() {
  const store = useAuthStore()
  const isLoggedIn = computed(() => store.isAuthenticated)

  return {
    user: store.user,
    loading: store.loading,
    isLoggedIn,
    login: store.login,
    register: store.register,
    logout: store.logout,
  }
}

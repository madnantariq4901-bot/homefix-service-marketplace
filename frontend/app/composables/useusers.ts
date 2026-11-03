export const useUsers = () => {
  const userStore = useUserStore()

  const fetchProfile = async () => {
    return await userStore.fetchMyProfile()
  }

  return {
    userStore,
    fetchProfile,
  }
}
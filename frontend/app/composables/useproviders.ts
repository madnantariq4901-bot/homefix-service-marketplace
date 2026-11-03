export const useProviders = () => {
  const providersStore = useProvidersStore()

  const fetchMyProfile = async () => {
    return await providersStore.fetchMyProfile()
  }

  const addSkill = async (
    categoryId: number,
    yearsExperience: number
  ) => {
    return await providersStore.addSkill({
      category_id: categoryId,
      years_experience: yearsExperience,
    })
  }

  const updateAvailability = async (
    isAvailable: boolean
  ) => {
    return await providersStore.updateAvailability(
      isAvailable
    )
  }

  const updateLocation = async (
    lat: number,
    lng: number
  ) => {
    return await providersStore.updateLocation({
      lat,
      lng,
    })
  }

  return {
    providersStore,
    fetchMyProfile,
    addSkill,
    updateAvailability,
    updateLocation,
  }
}
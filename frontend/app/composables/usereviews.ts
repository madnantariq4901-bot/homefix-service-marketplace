export const useReviews = () => {
  const reviewsStore = useReviewsStore()

  const fetchProviderReviews = async (
    providerId: number
  ) => {
    return await reviewsStore.fetchProviderReviews(
      providerId
    )
  }

  return {
    reviewsStore,
    fetchProviderReviews,
  }
}
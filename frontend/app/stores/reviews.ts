import { defineStore } from "pinia"

import {
  reviewsService,
  type Review,
} from "~/services/reviews.service"

export const useReviewsStore = defineStore("reviews", () => {
  const reviews = ref<Review[]>([])
  const loading = ref(false)
  const error = ref("")

  async function fetchProviderReviews(providerId: number) {
    loading.value = true
    error.value = ""

    try {
      reviews.value =
        await reviewsService.getProviderReviews(providerId)
    } catch (err: any) {
      error.value =
        err?.data?.detail ||
        "Unable to load reviews."
    } finally {
      loading.value = false
    }
  }

  return {
    reviews,
    loading,
    error,
    fetchProviderReviews,
  }
})
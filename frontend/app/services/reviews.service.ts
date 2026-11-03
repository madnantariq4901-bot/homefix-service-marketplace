import { api } from "./api"
import type { Review } from "~/types/review"

export type { Review } from "~/types/review"

export const reviewsService = {
  async getProviderReviews(providerId: number) {
    return await api<Review[]>(`/providers/${providerId}/reviews`, { method: "GET" })
  },
}

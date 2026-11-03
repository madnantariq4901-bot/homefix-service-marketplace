export interface Review {
  id: number
  job_id: number
  provider_id: number
  rating: number
  comment: string | null
}

export interface ReviewCreate {
  rating: number
  comment?: string
}

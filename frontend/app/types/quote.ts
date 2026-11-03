export interface Quote {
  id: number
  job_id: number
  provider_id: number
  quoted_amount: number
  provider_name: string
  provider_rating_avg: number
  provider_rating_count: number
}

export interface QuoteCreate {
  quoted_amount: number
}

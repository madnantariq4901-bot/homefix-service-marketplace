import { api } from "./api"
import type { Quote } from "~/types/quote"
import type { Job } from "~/types/job"

export type { Quote, QuoteCreate } from "~/types/quote"

export const quotesService = {
  async getJobQuotes(jobId: number) {
    return await api<Quote[]>(`/jobs/${jobId}/quotes`, { method: "GET" })
  },

  async acceptQuote(jobId: number, quoteId: number) {
    return await api<Job>(`/jobs/${jobId}/quotes/${quoteId}/accept`, { method: "POST" })
  },
}

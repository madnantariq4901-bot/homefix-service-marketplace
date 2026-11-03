import { ref } from "vue"
import { defineStore } from "pinia"

import { quotesService } from "~/services/quotes.service"
import type { Quote } from "~/types/quote"
import type { Job } from "~/types/job"

export const useQuotesStore = defineStore("quotes", () => {
  const quotes = ref<Quote[]>([])
  const loading = ref(false)
  const error = ref("")

  async function fetchJobQuotes(jobId: number) {
    loading.value = true
    error.value = ""
    try {
      quotes.value = await quotesService.getJobQuotes(jobId)
      return quotes.value
    } catch (err: any) {
      error.value = err?.data?.detail || "Unable to load quotes."
      quotes.value = []
      throw err
    } finally {
      loading.value = false
    }
  }

  async function acceptQuote(jobId: number, quoteId: number): Promise<Job> {
    loading.value = true
    error.value = ""
    try {
      return await quotesService.acceptQuote(jobId, quoteId)
    } catch (err: any) {
      error.value = err?.data?.detail || "Unable to accept quote."
      throw err
    } finally {
      loading.value = false
    }
  }

  return { quotes, loading, error, fetchJobQuotes, acceptQuote }
})

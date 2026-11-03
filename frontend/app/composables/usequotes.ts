export const useQuotes = () => {
  const quotesStore = useQuotesStore()

  const fetchJobQuotes = async (
    jobId: number
  ) => {
    return await quotesStore.fetchJobQuotes(jobId)
  }

  return {
    quotesStore,
    fetchJobQuotes,
  }
}
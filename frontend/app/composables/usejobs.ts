import type { JobCreate, JobStatus } from "~/types/job"
import type { ReviewCreate } from "~/types/review"

export const useJobs = () => {
  const jobsStore = useJobsStore()

  return {
    jobsStore,
    fetchMyJobs: jobsStore.fetchMyJobs,
    fetchAvailableJobs: jobsStore.fetchAvailableJobs,
    fetchJob: jobsStore.fetchJob,
    createJob: (data: JobCreate) => jobsStore.createJob(data),
    submitQuote: (jobId: number, amount: number) => jobsStore.submitQuote(jobId, amount),
    updateStatus: (jobId: number, status: JobStatus, finalAmount?: number) =>
      jobsStore.updateStatus(jobId, { status, ...(finalAmount === undefined ? {} : { final_amount: finalAmount }) }),
    createReview: (jobId: number, rating: number, comment?: string) =>
      jobsStore.createReview(jobId, { rating, ...(comment ? { comment } : {}) } satisfies ReviewCreate),
  }
}

import { defineStore } from "pinia"

import { jobsService } from "~/services/jobs.service"
import type { Job, JobAdminUpdate, JobCreate, JobStatus, JobStatusUpdate } from "~/types/job"
import type { Review, ReviewCreate } from "~/types/review"

export const useJobsStore = defineStore("jobs", () => {
  const jobs = ref<Job[]>([])
  const availableJobs = ref<Job[]>([])
  const currentJob = ref<Job | null>(null)
  const loading = ref(false)
  const error = ref("")

  async function fetchMyJobs() {
    loading.value = true
    error.value = ""
    try {
      jobs.value = await jobsService.getMyJobs()
      return jobs.value
    } catch (err: any) {
      error.value = err?.data?.detail || "Unable to load jobs."
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchAvailableJobs() {
    loading.value = true
    error.value = ""
    try {
      availableJobs.value = await jobsService.getAvailableJobs()
      return availableJobs.value
    } catch (err: any) {
      error.value = err?.data?.detail || "Unable to load available jobs."
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchJob(jobId: number) {
    loading.value = true
    error.value = ""
    try {
      currentJob.value = await jobsService.getJob(jobId)
      return currentJob.value
    } catch (err: any) {
      error.value = err?.data?.detail || "Unable to load job."
      currentJob.value = null
      throw err
    } finally {
      loading.value = false
    }
  }

  async function deleteJob(jobId: number) {
    error.value = ""
    try {
      await jobsService.deleteJob(jobId)
      jobs.value = jobs.value.filter(job => job.id !== jobId)
      availableJobs.value = availableJobs.value.filter(job => job.id !== jobId)
      if (currentJob.value?.id === jobId) currentJob.value = null
    } catch (err: any) {
      error.value = err?.data?.detail || "Unable to delete job."
      throw err
    }
  }

  async function updateJobDetails(jobId: number, data: JobAdminUpdate) {
    error.value = ""
    try {
      const updatedJob = await jobsService.updateJobDetails(jobId, data)
      jobs.value = jobs.value.map(job => job.id === jobId ? updatedJob : job)
      availableJobs.value = availableJobs.value.map(job => job.id === jobId ? updatedJob : job)
      if (currentJob.value?.id === jobId) currentJob.value = updatedJob
      return updatedJob
    } catch (err: any) {
      error.value = err?.data?.detail || "Unable to update job details."
      throw err
    }
  }

  async function createJob(data: JobCreate) {
    loading.value = true
    error.value = ""
    try {
      const job = await jobsService.createJob(data)
      jobs.value.unshift(job)
      return job
    } catch (err: any) {
      error.value = err?.data?.detail || "Unable to create job."
      throw err
    } finally {
      loading.value = false
    }
  }

  async function uploadAttachments(jobId: number, files: File[]) {
    error.value = ""
    try {
      return await jobsService.uploadAttachments(jobId, files)
    } catch (err: any) {
      error.value = err?.data?.detail || "Unable to upload job attachments."
      throw err
    }
  }

  async function submitQuote(jobId: number, amount: number) {
    loading.value = true
    error.value = ""
    try {
      currentJob.value = await jobsService.createQuote(jobId, amount)
      return currentJob.value
    } catch (err: any) {
      error.value = err?.data?.detail || "Unable to submit quote."
      throw err
    } finally {
      loading.value = false
    }
  }

  async function updateStatus(jobId: number, data: JobStatusUpdate) {
    loading.value = true
    error.value = ""
    try {
      currentJob.value = await jobsService.updateStatus(jobId, data)
      return currentJob.value
    } catch (err: any) {
      error.value = err?.data?.detail || "Unable to update job."
      throw err
    } finally {
      loading.value = false
    }
  }

  async function createReview(jobId: number, data: ReviewCreate): Promise<Review> {
    loading.value = true
    error.value = ""
    try {
      return await jobsService.createReview(jobId, data)
    } catch (err: any) {
      error.value = err?.data?.detail || "Unable to submit review."
      throw err
    } finally {
      loading.value = false
    }
  }

  async function refreshJobLists() {
    await fetchMyJobs()
    if (useAuthStore().user?.role === "provider") {
      await fetchAvailableJobs()
    } else {
      availableJobs.value = []
    }
  }

  return {
    jobs,
    availableJobs,
    currentJob,
    loading,
    error,
    fetchMyJobs,
    fetchAvailableJobs,
    fetchJob,
    deleteJob,
    updateJobDetails,
    createJob,
    uploadAttachments,
    submitQuote,
    updateStatus,
    createReview,
    refreshJobLists,
  }
})

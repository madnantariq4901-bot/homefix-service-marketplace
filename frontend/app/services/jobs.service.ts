import { api } from "./api"
import type { Job, JobAdminUpdate, JobAttachment, JobCreate, JobStatusUpdate } from "~/types/job"
import type { Review, ReviewCreate } from "~/types/review"

export type { Job, JobAdminUpdate, JobCreate, JobStatus, JobStatusUpdate } from "~/types/job"

export const jobsService = {
  async createJob(data: JobCreate) {
    return await api<Job>("/jobs", { method: "POST", body: data })
  },

  async uploadAttachments(jobId: number, files: File[]) {
    const body = new FormData()
    files.forEach(file => body.append("files", file, file.name))
    return await api<JobAttachment[]>(`/jobs/${jobId}/attachments`, { method: "POST", body })
  },

  async getAttachmentFile(jobId: number, attachmentId: number) {
    return await api<Blob>(`/jobs/${jobId}/attachments/${attachmentId}/file`, {
      method: "GET",
      responseType: "blob",
    })
  },

  async getMyJobs() {
    return await api<Job[]>("/jobs/mine", { method: "GET" })
  },

  async getAvailableJobs() {
    return await api<Job[]>("/jobs/available", { method: "GET" })
  },

  async getJob(jobId: number) {
    return await api<Job>(`/jobs/${jobId}`, { method: "GET" })
  },

  async deleteJob(jobId: number) {
    return await api<void>(`/jobs/${jobId}`, { method: "DELETE" })
  },

  async updateJobDetails(jobId: number, data: JobAdminUpdate) {
    return await api<Job>(`/jobs/${jobId}`, { method: "PATCH", body: data })
  },

  async approachProvider(jobId: number, providerId: number) {
    return await api<{ job_id: number; provider_id: number; notification_id: number; message: string }>(
      `/jobs/${jobId}/approach`,
      { method: "POST", body: { provider_id: providerId } },
    )
  },

  async updateStatus(jobId: number, data: JobStatusUpdate) {
    return await api<Job>(`/jobs/${jobId}/status`, { method: "PATCH", body: data })
  },

  async createQuote(jobId: number, quotedAmount: number) {
    return await api<Job>(`/jobs/${jobId}/quote`, {
      method: "POST",
      body: { quoted_amount: quotedAmount },
    })
  },

  async createReview(jobId: number, data: ReviewCreate) {
    return await api<Review>(`/jobs/${jobId}/review`, { method: "POST", body: data })
  },
}

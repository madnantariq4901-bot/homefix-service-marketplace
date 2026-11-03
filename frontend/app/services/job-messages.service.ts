import { api } from "./api"
import type { JobMessage } from "~/types/jobMessage"

export const jobMessagesService = {
  async list(jobId: number) {
    return await api<JobMessage[]>(`/jobs/${jobId}/messages`, { method: "GET" })
  },

  async send(jobId: number, body: { body: string } | { latitude: number; longitude: number }) {
    return await api<JobMessage>(`/jobs/${jobId}/messages`, { method: "POST", body })
  },
}
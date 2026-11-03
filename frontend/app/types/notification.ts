export interface Notification {
  id: number
  job_id: number
  message: string
  is_read: boolean
  created_at: string
  user_id?: number
}

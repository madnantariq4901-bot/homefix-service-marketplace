export interface JobMessage {
  id: number
  job_id: number
  sender_id: number
  sender_name: string
  body: string | null
  latitude: number | null
  longitude: number | null
  created_at: string
}
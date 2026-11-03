export type JobStatus =
  | "requested"
  | "quoted"
  | "accepted"
  | "en_route"
  | "in_progress"
  | "completed"
  | "cancelled"

export interface Job {
  id: number
  customer_id: number
  provider_id: number | null
  category_id: number
  description: string
  address: string
  lat: number | null
  lng: number | null
  status: JobStatus
  quoted_amount: number | null
  final_amount: number | null
  completion_requested: boolean
  has_review: boolean
  customer_name: string | null
  customer_email: string | null
  provider_name: string | null
  provider_email: string | null
  attachments?: JobAttachment[]
}

export interface JobAttachment {
  id: number
  original_name: string
  media_type: string
  size_bytes: number
}

export interface JobCreate {
  category_id: number
  preferred_provider_id?: number
  description: string
  address: string
  lat?: number
  lng?: number
}

export interface JobStatusUpdate {
  status: JobStatus
  final_amount?: number
}

export interface JobAdminUpdate {
  category_id: number
  description: string
  address: string
  lat: number | null
  lng: number | null
}

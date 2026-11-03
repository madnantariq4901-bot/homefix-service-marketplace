import type { CategoryName } from "~/types/category"

export interface ProviderSkill {
  id: number
  category_id: number
  years_experience: number
}

export interface Provider {
  id: number
  user_id: number
  is_verified: boolean
  is_available: boolean
  current_lat: number | null
  current_lng: number | null
  rating_avg: number
  rating_count: number
  identity_documents_submitted: boolean
  completed_job_count: number
  skills: ProviderSkill[]
}

export interface SkillCreate {
  category_id: number
  years_experience: number
}

export interface AvailabilityUpdate {
  is_available: boolean
}

export interface LocationUpdate {
  lat: number
  lng: number
}

export interface ProviderDirectoryItem {
  id: number
  user_id: number
  full_name: string
  is_verified: boolean
  is_available: boolean
  rating_avg: number
  rating_count: number
  completed_job_count: number
  skills: ProviderSkill[]
}

export interface ProviderAdminDirectoryItem extends ProviderDirectoryItem {
  identity_documents_submitted: boolean
}

export interface PublicProviderSkill {
  category_id: number
  category: CategoryName
  years_experience: number
}

export interface PublicProvider {
  id: number
  full_name: string
  is_verified: boolean
  is_available: boolean
  rating_avg: number
  rating_count: number
  completed_job_count: number
  skills: PublicProviderSkill[]
}

export interface PublicProviderFilters {
  category?: CategoryName
  available_only?: boolean
  limit?: number
  offset?: number
  search?: string
  sort_by?: "recommended" | "completed_jobs" | "rating" | "experience" | "name"
}

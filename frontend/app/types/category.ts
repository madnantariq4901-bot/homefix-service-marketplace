export type CategoryName = string

export interface Category {
  id: number
  name: CategoryName
  base_hourly_rate: number
  description: string | null
}

export interface CategoryCreate {
  name: CategoryName
  base_hourly_rate: number
  description?: string
}

export interface CategoryUpdate {
  name?: CategoryName
  base_hourly_rate?: number
  description?: string | null
}

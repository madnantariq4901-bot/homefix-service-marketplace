export interface User {
  id: number
  email: string
  full_name: string
  phone: string | null
  role: "customer" | "provider" | "admin"
}

export interface UserUpdate {
  full_name?: string
  phone?: string | null
}

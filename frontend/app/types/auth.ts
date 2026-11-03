import type { User } from "~/types/user"

export interface LoginData {
  email: string
  password: string
}

export interface RegisterData {
  email: string
  password: string
  full_name: string
  phone?: string
  role: "customer" | "provider"
}

export interface TokenResponse {
  access_token: string
  token_type: "bearer"
}

export type RegisteredUser = User

import { api } from "./api"
import type { LoginData, RegisterData, TokenResponse } from "~/types/auth"
import type { User } from "~/types/user"

export type { LoginData, RegisterData, TokenResponse } from "~/types/auth"

export const authService = {
  async login(data: LoginData) {
    return await api<TokenResponse>("/auth/login", {
      method: "POST",
      body: data,
    })
  },

  async register(data: RegisterData) {
    return await api<User>("/auth/signup", {
      method: "POST",
      body: data,
    })
  },

  async requestPasswordReset(email: string) {
    return await api<{ message: string }>("/auth/forgot-password", {
      method: "POST",
      body: { email },
    })
  },

  async resetPassword(token: string, newPassword: string) {
    return await api<{ message: string }>("/auth/reset-password", {
      method: "POST",
      body: { token, new_password: newPassword },
    })
  },
}

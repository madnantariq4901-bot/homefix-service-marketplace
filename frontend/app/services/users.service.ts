import { api } from "./api"
import type { User, UserUpdate } from "~/types/user"

export type { User } from "~/types/user"

export const usersService = {
  async getMyProfile(token?: string) {
    return await api<User>("/users/me", {
      method: "GET",
      headers: token ? { Authorization: `Bearer ${token}` } : undefined,
    })
  },

  async updateMyProfile(data: UserUpdate) {
    return await api<User>("/users/me", { method: "PATCH", body: data })
  },
}

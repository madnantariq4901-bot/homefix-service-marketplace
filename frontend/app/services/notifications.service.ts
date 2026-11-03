import { api } from "./api"
import type { Notification } from "~/types/notification"

export const notificationsService = {
  async getMine() {
    return await api<Notification[]>("/notifications/mine", { method: "GET" })
  },

  async getAdminAll() {
    return await api<Notification[]>("/notifications/admin/all", { method: "GET" })
  },

  async markRead(notificationId: number) {
    return await api<Notification>(`/notifications/${notificationId}/read`, { method: "PATCH" })
  },
}

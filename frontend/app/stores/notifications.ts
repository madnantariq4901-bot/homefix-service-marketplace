import { defineStore } from "pinia"

import { notificationsService } from "~/services/notifications.service"
import type { Notification } from "~/types/notification"

export const useNotificationsStore = defineStore("notifications", () => {
  const notifications = ref<Notification[]>([])
  const loading = ref(false)
  const error = ref("")
  const unreadCount = computed(() => notifications.value.filter(item => !item.is_read).length)

  async function fetchMine() {
    loading.value = true
    error.value = ""
    try {
      notifications.value = await notificationsService.getMine()
      return notifications.value
    } catch (err: any) {
      error.value = err?.data?.detail || "Unable to load notifications."
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchAdminAll() {
    loading.value = true
    error.value = ""
    try {
      notifications.value = await notificationsService.getAdminAll()
      return notifications.value
    } catch (err: any) {
      error.value = err?.data?.detail || "Unable to load administrative notifications."
      throw err
    } finally {
      loading.value = false
    }
  }

  async function markRead(notificationId: number) {
    error.value = ""
    try {
      const notification = await notificationsService.markRead(notificationId)
      const index = notifications.value.findIndex(item => item.id === notificationId)
      if (index !== -1) notifications.value[index] = notification
      return notification
    } catch (err: any) {
      error.value = err?.data?.detail || "Unable to mark notification as read."
      throw err
    }
  }

  function clear() {
    notifications.value = []
    error.value = ""
  }

  return { notifications, loading, error, unreadCount, fetchMine, fetchAdminAll, markRead, clear }
})

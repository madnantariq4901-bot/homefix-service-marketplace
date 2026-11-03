<script setup lang="ts">
definePageMeta({ middleware: "auth" })

const authStore = useAuthStore()
const notificationsStore = useNotificationsStore()
const actionError = ref("")

onMounted(async () => {
  try {
    if (!authStore.user) await authStore.loadCurrentUser()
    if (authStore.user?.role === "admin") await notificationsStore.fetchAdminAll()
    else await notificationsStore.fetchMine()
  } catch {
    actionError.value = notificationsStore.error
  }
})

async function openNotification(notificationId: number) {
  actionError.value = ""
  try {
    await notificationsStore.markRead(notificationId)
  } catch {
    actionError.value = notificationsStore.error
  }
}
</script>

<template>
  <main class="notifications-page container">
    <header class="page-heading">
      <div>
        <p class="eyebrow">Updates</p>
        <h1>Notifications</h1>
        <p>Updates about your jobs appear here.</p>
      </div>
      <span class="unread-count">{{ notificationsStore.unreadCount }} unread</span>
    </header>

    <AppAlert v-if="actionError || notificationsStore.error" type="error">
      {{ actionError || notificationsStore.error }}
    </AppAlert>
    <AppLoader v-if="notificationsStore.loading" />
    <div v-else-if="!notificationsStore.notifications.length" class="empty-state">
      <h2>You’re all caught up</h2>
      <p>When there are updates about your jobs, you’ll find them here.</p>
    </div>
    <ul v-else class="notification-list">
      <li
        v-for="notification in notificationsStore.notifications"
        :key="notification.id"
        :class="{ unread: !notification.is_read }"
      >
        <div>
          <p>{{ notification.message }}</p>
          <time :datetime="notification.created_at">{{ new Date(notification.created_at).toLocaleString() }}</time>
          <small v-if="authStore.user?.role === 'admin' && notification.user_id">Recipient user #{{ notification.user_id }}</small>
        </div>
        <div class="notification-actions">
          <NuxtLink :to="`/jobs/${notification.job_id}`" @click="openNotification(notification.id)">View job</NuxtLink>
          <button
            v-if="!notification.is_read"
            type="button"
            :disabled="notificationsStore.loading"
            @click="openNotification(notification.id)"
          >Mark read</button>
        </div>
      </li>
    </ul>
  </main>
</template>

<style scoped>
.notifications-page { max-width: 900px; padding-top: 32px; padding-bottom: 48px; }
.page-heading { display: flex; justify-content: space-between; align-items: flex-end; gap: 16px; margin-bottom: 24px; }
.page-heading h1 { margin: 4px 0 8px; }
.page-heading p { margin-top: 0; color: var(--color-muted); }
.eyebrow { margin: 0; color: var(--color-primary); font-size: 13px; font-weight: 700; text-transform: uppercase; letter-spacing: .05em; }
.unread-count { white-space: nowrap; color: var(--color-muted); font-size: 14px; }
.notification-list { display: grid; gap: 10px; padding: 0; list-style: none; }
.notification-list li { display: flex; justify-content: space-between; align-items: center; gap: 20px; padding: 18px; border: 1px solid var(--color-border); border-radius: 10px; background: var(--color-surface); }
.notification-list li.unread { border-left: 4px solid var(--color-primary); }
.notification-list p { margin: 0 0 7px; }
.notification-list time { color: var(--color-muted); font-size: 13px; }
.notification-actions { display: flex; align-items: center; gap: 14px; white-space: nowrap; }
.notification-actions a { color: var(--color-primary); }
.notification-actions button { padding: 5px 10px; }
.empty-state { padding: 36px; text-align: center; border: 1px dashed var(--color-border); border-radius: 10px; }
.empty-state p { color: var(--color-muted); }
@media (max-width: 600px) { .page-heading, .notification-list li { align-items: flex-start; flex-direction: column; } }
</style>

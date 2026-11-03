b<script setup lang="ts">
const authStore = useAuthStore()
const notificationsStore = useNotificationsStore()
const route = useRoute()
const menuOpen = ref(false)
let refreshTimer: ReturnType<typeof setInterval> | undefined

async function refreshNotifications() {
  if (!authStore.isAuthenticated) {
    notificationsStore.clear()
    return
  }
  try {
    if (authStore.user?.role === 'admin') {
      await notificationsStore.fetchAdminAll()
    } else {
      await notificationsStore.fetchMine()
    }
  } catch {
    // The notifications page exposes the store's error message.
  }
}

onMounted(async () => {
  if (authStore.token && !authStore.user) {
    await authStore.loadCurrentUser().catch(() => undefined)
  }
  await refreshNotifications()
  refreshTimer = setInterval(() => { void refreshNotifications() }, 20000)
})

// Close the mobile menu after every navigation.
watch(() => route.fullPath, () => { menuOpen.value = false })
watch(() => authStore.isAuthenticated, () => { void refreshNotifications() })
onBeforeUnmount(() => {
  if (refreshTimer) clearInterval(refreshTimer)
})
</script>

<template>
  <header class="site-header">
    <div class="container bar">
      <NuxtLink class="brand" to="/" aria-label="Home">
        <AppLogo />
      </NuxtLink>

      <button
        type="button"
        class="menu-toggle"
        :aria-expanded="menuOpen"
        aria-controls="main-nav"
        aria-label="Toggle menu"
        @click="menuOpen = !menuOpen"
      >
        {{ menuOpen ? "✕" : "☰" }}
      </button>

      <nav id="main-nav" :class="{ open: menuOpen }">
        <NuxtLink to="/categories">Services</NuxtLink>
        <NuxtLink to="/providers/browse">Find a provider</NuxtLink>
        <NuxtLink to="/about">About</NuxtLink>
        <NuxtLink to="/contact">Contact</NuxtLink>

        <template v-if="authStore.isAuthenticated">
          <span class="divider" aria-hidden="true" />
          <NuxtLink to="/dashboard">Dashboard</NuxtLink>
          <NuxtLink to="/jobs">Jobs</NuxtLink>
          <NuxtLink to="/notifications" class="notification-link">
            Notifications
            <span v-if="notificationsStore.unreadCount" class="notification-count">{{ notificationsStore.unreadCount }}</span>
          </NuxtLink>
          <NuxtLink v-if="authStore.user?.role === 'provider'" to="/providers">My provider profile</NuxtLink>
          <NuxtLink to="/profiles">My profile</NuxtLink>
          <NuxtLink v-if="authStore.user?.role === 'admin'" to="/admin/providers">Provider badges</NuxtLink>
          <NuxtLink v-if="authStore.user?.role === 'admin'" to="/admin/services">Manage services</NuxtLink>
          <button type="button" class="signout" @click="authStore.logout">Sign out</button>
        </template>
        <template v-else>
          <span class="divider" aria-hidden="true" />
          <NuxtLink to="/auth/login">Sign in</NuxtLink>
          <NuxtLink to="/auth/register" class="btn btn-accent cta">Get started</NuxtLink>
        </template>
      </nav>
    </div>
  </header>
</template>

<style scoped>
.site-header { position: sticky; top: 0; z-index: 20; background: rgb(255 255 255 / 96%); backdrop-filter: blur(12px); border-bottom: 1px solid var(--color-border); }
.bar { display: flex; justify-content: space-between; align-items: center; gap: 20px; min-height: 64px; }
.brand { text-decoration: none; }
nav { display: flex; align-items: center; gap: 21px; flex-wrap: wrap; }
nav a { text-decoration: none; font-size: 14px; font-weight: 600; color: var(--color-text); }
nav a:hover { color: var(--color-primary); }
nav a.router-link-exact-active:not(.btn) { color: var(--color-primary); }
.notification-link { display: inline-flex; align-items: center; gap: 6px; }
.notification-count { display: inline-grid; min-width: 19px; height: 19px; place-items: center; padding: 0 5px; border-radius: 999px; color: white; background: var(--color-primary); font-size: 11px; }
.divider { width: 1px; height: 22px; background: var(--color-border); }
.cta { padding: 8px 16px; color: #fff; }
.cta:hover { color: #fff; }
.signout { padding: 7px 14px; color: var(--color-text); background: transparent; border-color: var(--color-border); }
.signout:hover:not(:disabled) { background: var(--color-page); }
.menu-toggle { display: none; padding: 6px 12px; font-size: 18px; color: var(--color-text); background: transparent; border-color: var(--color-border); }
.menu-toggle:hover:not(:disabled) { background: var(--color-page); }

@media (max-width: 900px) {
  .menu-toggle { display: inline-block; }
  nav { display: none; position: absolute; top: 64px; left: 0; right: 0; flex-direction: column; align-items: stretch; gap: 4px; padding: 12px max(16px, calc((100% - var(--container)) / 2)) 18px; background: #fff; border-bottom: 1px solid var(--color-border); box-shadow: var(--shadow-md); }
  nav.open { display: flex; }
  nav a { padding: 10px 4px; }
  .divider { width: 100%; height: 1px; margin: 4px 0; }
  .cta { text-align: center; margin-top: 4px; }
}
</style>

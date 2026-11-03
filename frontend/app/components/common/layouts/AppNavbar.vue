<script setup lang="ts">
const userStore = useUserStore()

onMounted(async () => {
  if (!userStore.user) {
    await userStore.fetchMyProfile()
  }
})
</script>

<template>
  <div class="navbar">
    <div>
      <NuxtLink to="/dashboard">
        Service Marketplace
      </NuxtLink>
    </div>

    <div class="user">
      <span v-if="userStore.user">
        {{ userStore.user.full_name }}
      </span>

      <NuxtLink to="/profiles">
        Profile
      </NuxtLink>
    </div>
  </div>
</template>

<style scoped>
.navbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 25px;
  border-bottom: 1px solid #ddd;
}

.navbar a {
  text-decoration: none;
  color: inherit;
}

.user {
  display: flex;
  gap: 18px;
  align-items: center;
}
</style>
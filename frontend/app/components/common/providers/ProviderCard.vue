<script setup lang="ts">
import type { ProviderDirectoryItem } from "~/types/provider"

defineProps<{
  provider: ProviderDirectoryItem
}>()
</script>

<template>
  <div class="provider-card">
    <div class="provider-header">
      <h2>{{ provider.full_name }}</h2>

      <span
        :class="{
          available: provider.is_available,
          unavailable: !provider.is_available,
        }"
      >
        {{ provider.is_available ? "Available" : "Unavailable" }}
      </span>
    </div>

    <p>
      <strong>Rating:</strong>
      {{ provider.rating_avg.toFixed(1) }}
      ({{ provider.rating_count }} reviews)
    </p>

    <p>
      <strong>Verified:</strong>
      {{ provider.is_verified ? "Yes" : "No" }}
    </p>

    <p>
      <strong>Skills:</strong>
      {{ provider.skills.length }}
    </p>

    <NuxtLink :to="`/providers/${provider.id}`">
      View profile
    </NuxtLink>
  </div>
</template>

<style scoped>
.provider-card {
  padding: 20px;
  border: 1px solid #ddd;
  border-radius: 10px;
}

.provider-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.available {
  color: green;
}

.unavailable {
  color: red;
}

.provider-card a {
  display: inline-block;
  margin-top: 15px;
  padding: 10px 15px;
  background: #111;
  color: white;
  text-decoration: none;
  border-radius: 6px;
}
</style>
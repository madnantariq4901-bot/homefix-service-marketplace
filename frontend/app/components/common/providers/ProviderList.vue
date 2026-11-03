<script setup lang="ts">
import type { ProviderDirectoryItem } from "~/types/provider"

defineProps<{ providers: ProviderDirectoryItem[] }>()
</script>

<template>
  <div class="provider-list">
    <ProviderCard v-for="provider in providers" :key="provider.id" :provider="provider" />
  </div>
</template>

<style scoped>
.provider-list { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 16px; }
</style>

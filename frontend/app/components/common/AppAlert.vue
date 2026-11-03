<script setup lang="ts">
withDefaults(
  defineProps<{ type?: "success" | "error" | "info" | "warning" }>(),
  { type: "info" }
)

const icons = { success: "✓", error: "!", info: "i", warning: "⚠" }
</script>

<template>
  <div class="app-alert" :class="`alert-${type}`" role="alert">
    <span class="mark" aria-hidden="true">{{ icons[type] }}</span>
    <div class="body"><slot /></div>
  </div>
</template>

<style scoped>
.app-alert { display: flex; align-items: flex-start; gap: 12px; padding: 12px 16px; margin: 10px 0; border: 1px solid; border-left-width: 4px; border-radius: 10px; font-size: 15px; }
.mark { flex: none; display: grid; place-items: center; width: 22px; height: 22px; margin-top: 1px; font-size: 13px; font-weight: 800; color: #fff; border-radius: 50%; }
.body { flex: 1; }
.alert-success { background: #f0fdf4; border-color: #86efac; color: #14532d; }
.alert-success .mark { background: #16a34a; }
.alert-error { background: #fef2f2; border-color: #fca5a5; color: #7f1d1d; }
.alert-error .mark { background: #dc2626; }
.alert-info { background: #eff6ff; border-color: #93c5fd; color: #1e3a8a; }
.alert-info .mark { background: #2563eb; }
.alert-warning { background: #fffbeb; border-color: #fcd34d; color: #78350f; }
.alert-warning .mark { background: #d97706; }
</style>

<script setup lang="ts">
defineProps<{
  modelValue: string | number
  type?: string
  placeholder?: string
  label?: string
}>()

const emit = defineEmits<{
  "update:modelValue": [value: string]
}>()

const updateValue = (event: Event) => {
  const target = event.target as HTMLInputElement

  emit("update:modelValue", target.value)
}
</script>

<template>
  <div class="app-input">
    <label v-if="label">
      {{ label }}
    </label>

    <input
      :type="type || 'text'"
      :value="modelValue"
      :placeholder="placeholder"
      @input="updateValue"
    />
  </div>
</template>

<style scoped>
.app-input {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.app-input input {
  padding: 10px 12px;
  border: 1px solid #ccc;
  border-radius: 8px;
}
</style>
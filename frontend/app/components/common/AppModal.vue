<script setup lang="ts">
defineProps<{
  modelValue: boolean
  title?: string
}>()

const emit = defineEmits<{
  "update:modelValue": [value: boolean]
}>()

const close = () => {
  emit("update:modelValue", false)
}
</script>

<template>
  <div
    v-if="modelValue"
    class="modal-overlay"
    @click.self="close"
  >
    <div class="modal">
      <div class="modal-header">
        <h2>{{ title }}</h2>

        <button @click="close">
          ×
        </button>
      </div>

      <div class="modal-body">
        <slot />
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgb(0 0 0 / 45%);
}

.modal {
  width: min(500px, 90%);
  background: white;
  border-radius: 12px;
  padding: 20px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header button {
  border: none;
  background: none;
  font-size: 24px;
  cursor: pointer;
}
</style>
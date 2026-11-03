<script setup lang="ts">
import type { Category } from "~/services/categories.service"

defineProps<{
  categories: Category[]
}>()
</script>

<template>
  <div class="category-list">
    <CategoryCard
      v-for="category in categories"
      :key="category.id"
      :category="category"
    />
  </div>
</template>

<style scoped>
.category-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(270px, 1fr));
  gap: 20px;
}
</style>

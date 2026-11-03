import { defineStore } from "pinia"

import {
  categoriesService,
  type Category,
  type CategoryCreate,
} from "~/services/categories.service"

export const useCategoriesStore = defineStore("categories", () => {
  const categories = ref<Category[]>([])
  const loading = ref(false)
  const error = ref("")

  async function fetchCategories() {
    loading.value = true
    error.value = ""

    try {
      categories.value = await categoriesService.getCategories()
    } catch (err: any) {
      error.value =
        err?.data?.detail ||
        "Unable to load categories."
    } finally {
      loading.value = false
    }
  }

  async function createCategory(data: CategoryCreate) {
    loading.value = true
    error.value = ""

    try {
      const category = await categoriesService.createCategory(data)

      categories.value.push(category)

      return category
    } catch (err: any) {
      error.value =
        err?.data?.detail ||
        "Unable to create category."

      throw err
    } finally {
      loading.value = false
    }
  }

  return {
    categories,
    loading,
    error,
    fetchCategories,
    createCategory,
  }
})
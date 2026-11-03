import { api } from "./api"
import type { Category, CategoryCreate, CategoryUpdate } from "~/types/category"

export type { Category, CategoryCreate, CategoryUpdate } from "~/types/category"

export const categoriesService = {
  async getCategories() {
    return await api<Category[]>("/categories", { method: "GET" })
  },

  async createCategory(data: CategoryCreate) {
    return await api<Category>("/categories", { method: "POST", body: data })
  },

  async updateCategory(categoryId: number, data: CategoryUpdate) {
    return await api<Category>(`/categories/${categoryId}`, { method: "PATCH", body: data })
  },

  async deleteCategory(categoryId: number) {
    return await api<void>(`/categories/${categoryId}`, { method: "DELETE" })
  },
}

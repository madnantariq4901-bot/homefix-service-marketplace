export const useCategories = () => {
  const categoriesStore = useCategoriesStore()

  const fetchCategories = async () => {
    return await categoriesStore.fetchCategories()
  }

  return {
    categoriesStore,
    fetchCategories,
  }
}
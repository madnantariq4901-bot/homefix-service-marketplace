import { api } from "./api"
import type {
  AvailabilityUpdate,
  LocationUpdate,
  Provider,
  ProviderAdminDirectoryItem,
  ProviderDirectoryItem,
  ProviderSkill,
  PublicProvider,
  PublicProviderFilters,
  SkillCreate,
} from "~/types/provider"

export type {
  AvailabilityUpdate,
  LocationUpdate,
  Provider,
  ProviderAdminDirectoryItem,
  ProviderDirectoryItem,
  ProviderSkill,
  PublicProvider,
  PublicProviderFilters,
  SkillCreate,
} from "~/types/provider"

export const providersService = {
  // Public (no login): providers with a marketplace badge, with category names.
  async getPublicProviders(filters: PublicProviderFilters = {}) {
    return await api<PublicProvider[]>("/providers/public", { method: "GET", query: filters })
  },

  async getPublicProvider(providerId: number) {
    return await api<PublicProvider>(`/providers/public/${providerId}`, { method: "GET" })
  },

  async getProviders() {
    return await api<ProviderAdminDirectoryItem[]>("/providers", { method: "GET" })
  },

  async getProvider(providerId: number) {
    return await api<PublicProvider>(`/providers/${providerId}`, { method: "GET" })
  },

  async updateVerification(providerId: number, isVerified: boolean) {
    return await api<Provider>(`/providers/${providerId}/verification`, {
      method: "PATCH",
      body: { is_verified: isVerified },
    })
  },

  async getMyProfile() {
    return await api<Provider>("/providers/me", { method: "GET" })
  },

  async uploadIdentityDocuments(data: FormData) {
    return await api<Provider>("/providers/me/identity", { method: "POST", body: data })
  },

  async addSkill(data: SkillCreate) {
    return await api<ProviderSkill>("/providers/me/skills", { method: "POST", body: data })
  },

  async updateAvailability(data: AvailabilityUpdate) {
    return await api<Provider>("/providers/me/availability", { method: "PATCH", body: data })
  },

  async updateLocation(data: LocationUpdate) {
    return await api<Provider>("/providers/me/location", { method: "PATCH", body: data })
  },
}

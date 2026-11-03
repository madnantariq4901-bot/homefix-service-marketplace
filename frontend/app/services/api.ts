export async function api<T>(path: string, options: Record<string, any> = {}): Promise<T> {
  const config = useRuntimeConfig()
  const token = useCookie<string | null>("access_token")
  const headers: Record<string, string> = { ...(options.headers ?? {}) }

  if (token.value && !headers.Authorization) {
    headers.Authorization = `Bearer ${token.value}`
  }

  return await $fetch<T>(path, {
    baseURL: String(config.public.apiBaseUrl),
    ...options,
    headers,
  })
}

export function apiErrorMessage(error: unknown, fallback: string): string {
  if (!error || typeof error !== "object") return fallback

  const apiError = error as {
    data?: { detail?: unknown }
    response?: { status?: number }
  }
  const detail = apiError.data?.detail
  if (typeof detail === "string" && detail.trim()) return detail
  if (Array.isArray(detail)) {
    const messages = detail
      .map((item: unknown) => {
        if (item && typeof item === "object" && "msg" in item && typeof item.msg === "string") {
          return item.msg
        }
        return ""
      })
      .filter(Boolean)
    if (messages.length) return messages.join(" ")
  }

  if (apiError.response?.status) return `${fallback} (HTTP ${apiError.response.status})`
  return fallback
}

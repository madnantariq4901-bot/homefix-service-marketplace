const env = (
  globalThis as typeof globalThis & { process?: { env?: Record<string, string | undefined> } }
).process?.env ?? {}
const siteName = env.NUXT_PUBLIC_SITE_NAME || "HomeFix"

export default defineNuxtConfig({
  compatibilityDate: "2025-07-15",
  devtools: { enabled: true },
  vite: { server: { allowedHosts: true } },
  modules: ["@pinia/nuxt"],

  // FIX: components live in sub-folders (components/common/...). Without this,
  // Nuxt names them CommonAppAlert, CommonCategoriesCategoryCard, ... so
  // <AppAlert />, <CategoryList /> etc. fail with "Failed to resolve component".
  components: [{ path: "~/components", pathPrefix: false }],

  css: ["~/assets/mains.css", "~/assets/polish.css"],

  app: {
    head: {
      titleTemplate: `%s | ${siteName}`,
      meta: [
        { name: "viewport", content: "width=device-width, initial-scale=1" },
        {
          name: "description",
          content: `Find home cleaning, electrical, plumbing, AC, carpentry, and painting services with ${siteName}.`,
        },
        { name: "theme-color", content: "#142B50" },
      ],
      link: [
        { rel: "icon", type: "image/svg+xml", href: "/favicon.svg" },
        { rel: "icon", href: "/favicon.ico", sizes: "any" },
        { rel: "preconnect", href: "https://fonts.googleapis.com" },
        { rel: "preconnect", href: "https://fonts.gstatic.com", crossorigin: "" },
        {
          rel: "stylesheet",
          href: "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap",
        },
      ],
    },
  },

  runtimeConfig: {
    public: {
      apiBaseUrl: env.NUXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000",
      googleMapsApiKey: env.NUXT_PUBLIC_GOOGLE_MAPS_API_KEY || "",
      siteName,
      currencySymbol: env.NUXT_PUBLIC_CURRENCY_SYMBOL || "Rs",
      supportEmail: env.NUXT_PUBLIC_SUPPORT_EMAIL || "",
      supportPhone: env.NUXT_PUBLIC_SUPPORT_PHONE || "",
    },
  },
})

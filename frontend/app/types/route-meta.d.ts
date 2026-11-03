import "vue-router"

declare module "vue-router" {
  interface RouteMeta {
    requiredRole?: "customer" | "provider" | "admin" | Array<"customer" | "provider" | "admin">
  }
}

export {}

import { describe, expect, it } from "vitest"
import { getSafeRedirectPath } from "./authRedirect"

describe("getSafeRedirectPath", () => {
  it("keeps local application paths", () => {
    expect(getSafeRedirectPath("/jobs/create?category=4")).toBe("/jobs/create?category=4")
  })

  it("rejects external or malformed destinations", () => {
    expect(getSafeRedirectPath("https://example.com")).toBeNull()
    expect(getSafeRedirectPath("//example.com")).toBeNull()
    expect(getSafeRedirectPath("/\\\\example.com")).toBeNull()
    expect(getSafeRedirectPath(undefined)).toBeNull()
  })
})
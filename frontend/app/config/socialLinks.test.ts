import { describe, expect, it } from "vitest"
import { getConfiguredSocialLinks, type SocialLink } from "./socialLinks"

describe("getConfiguredSocialLinks", () => {
  it("omits links without a configured destination", () => {
    const links: SocialLink[] = [
      { name: "Facebook", url: "https://facebook.example/page", placeholder: "" },
      { name: "Instagram", url: "  ", placeholder: "" },
    ]

    expect(getConfiguredSocialLinks(links)).toEqual([links[0]])
  })

  it("returns no social links when all destinations are unconfigured", () => {
    expect(getConfiguredSocialLinks()).toEqual([])
  })
})

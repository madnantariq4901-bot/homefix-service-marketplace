
export interface SocialLink {
  name: 'Facebook' | 'Instagram' | 'YouTube' | 'TikTok' | 'GitHub' | 'LinkedIn'
  url: string
  placeholder: string
}

export const socialLinks: SocialLink[] = [
  {
    name: 'Facebook',
    url: '',
    placeholder: 'https://facebook.com/your-page',
  },
  {
    name: 'Instagram',
    url: '',
    placeholder: 'https://instagram.com/your-page',
  },
  {
    name: 'YouTube',
    url: '',
    placeholder: 'https://youtube.com/@your-channel',
  },
  {
    name: 'TikTok',
    url: '',
    placeholder: 'https://tiktok.com/@your-account',
  },
  {
    name: 'GitHub',
    url: '',
    placeholder: 'https://github.com/your-username',
  },
  {
    name: 'LinkedIn',
    url: '',
    placeholder: 'https://linkedin.com/in/your-profile',
  },
]

export function getConfiguredSocialLinks(links: readonly SocialLink[] = socialLinks) {
  return links.filter(item => item.url.trim())
}

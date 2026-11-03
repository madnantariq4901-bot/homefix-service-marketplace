# Frontend

From CMD, run these commands in this folder:

```bat
copy .env.example .env
npm ci
npm run dev
```

Open `http://localhost:3000`. Set `NUXT_PUBLIC_API_BASE_URL` in `.env` if the backend is running on another address.

For exact Google Places search, set `NUXT_PUBLIC_GOOGLE_MAPS_API_KEY` in `.env` to a Google Maps Platform key with Places API (New) enabled. Restrict the key to the website's HTTP referrers and the Places API. Without the key, address search uses OpenStreetMap data, which may not contain every local place.

Before deployment, set `NUXT_PUBLIC_API_BASE_URL`, `NUXT_PUBLIC_SITE_NAME`, `NUXT_PUBLIC_CURRENCY_SYMBOL`, `NUXT_PUBLIC_SUPPORT_EMAIL`, and `NUXT_PUBLIC_SUPPORT_PHONE` to the real public values for the site. Leave contact fields empty rather than publishing sample details.

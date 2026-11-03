<template>
  <div class="picker">
    <div class="search-row">
      <input
        v-model="query"
        type="text"
        autocomplete="off"
        placeholder="Search for a place or type its address"
        @input="onInput"
        @keydown.enter.prevent="searchNow"
      />
      <button type="button" @click="useMyLocation">My location</button>
    </div>

    <ul v-if="suggestions.length" class="suggestions">
      <li v-for="(s, i) in suggestions" :key="i" @click="choose(s)">{{ s.label }}</li>
    </ul>

    <section class="map-panel" aria-label="Interactive location map">
      <header class="map-heading">
        <div>
          <h3>Choose on the live map</h3>
          <p>Pan and zoom to the service location, then click to place the pin.</p>
        </div>
        <span class="live-badge"><span aria-hidden="true"></span> Live map</span>
      </header>
      <div ref="mapElement" class="location-map" role="application" aria-label="Interactive map for choosing a service location"></div>
      <p class="map-attribution">Map data © OpenStreetMap contributors</p>
    </section>
    <div class="coordinates-row">
      <label for="location-coordinates">Or paste Google Maps coordinates</label>
      <div class="search-row">
        <input
          id="location-coordinates"
          v-model="coordinateInput"
          type="text"
          inputmode="decimal"
          autocomplete="off"
          placeholder="e.g. 30.19438, 71.53746"
          @input="onCoordinatesInput"
        />
        <button type="button" @click="applyCoordinates">Use coordinates</button>
      </div>
    </div>

    <p class="status" :class="{ ok: confirmed }">
      {{ status || "Choose a search result, click the map, paste coordinates, or use My location." }}
    </p>
    <p v-if="confirmed" class="selected-coordinates">
      Pin: {{ selectedCoordinates }}
    </p>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue"
// @ts-ignore Leaflet's CSS file has no TypeScript declaration.
import "leaflet/dist/leaflet.css"

type Picked = { address: string; city: string; latitude: number; longitude: number }
type Suggestion = { label: string; city: string; lat: number; lng: number; placeId?: string }

const emit = defineEmits<{
  (e: "picked", v: Picked): void
  (e: "cleared"): void
}>()
const config = useRuntimeConfig()

const query = ref("")
const coordinateInput = ref("")
const status = ref("")
const confirmed = ref(false)
const suggestions = ref<Suggestion[]>([])
const mapElement = ref<HTMLElement | null>(null)
const selectedCoordinates = ref("")
let timer: any = null
let requestId = 0
let L: any
let map: any
let marker: any
let markerIcon: any

const BIAS_LAT = 30.1575
const BIAS_LON = 71.5249

function distanceKm(lat: number, lon: number): number {
  const dLat = (lat - BIAS_LAT) * (Math.PI / 180)
  const dLon = (lon - BIAS_LON) * (Math.PI / 180)
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(BIAS_LAT * (Math.PI / 180)) *
      Math.cos(lat * (Math.PI / 180)) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2)
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
  return 6371 * c
}

function scoreSuggestion(s: Suggestion): number {
  const city = (s.city || "").toLowerCase()
  const label = (s.label || "").toLowerCase()
  const close = distanceKm(s.lat, s.lng)
  const inPakistan = /pakistan|punjab|lahore|multan|karachi|islamabad|rawalpindi|faisalabad|gujranwala/.test(label + " " + city)
  const exactName = label.includes(query.value.trim().toLowerCase())
  return (inPakistan ? 10000 : 0) - close + (exactName ? 1000 : 0)
}

function normalizeResults(list: Suggestion[]): Suggestion[] {
  const seen = new Set<string>()
  return [...list]
    .filter((item) => Number.isFinite(item.lat) && Number.isFinite(item.lng))
    .filter((item) => {
      const key = `${item.label}|${item.lat.toFixed(6)}|${item.lng.toFixed(6)}`
      if (seen.has(key)) return false
      seen.add(key)
      return true
    })
    .sort((a, b) => scoreSuggestion(b) - scoreSuggestion(a))
}

function updateMap(lat: number, lng: number, zoom = 16) {
  if (!map || !L) return
  if (marker) {
    marker.setLatLng([lat, lng])
  } else {
    marker = L.marker([lat, lng], { draggable: true, icon: markerIcon }).addTo(map)
    marker.on("dragend", () => {
      const point = marker.getLatLng()
      void selectMapLocation(point.lat, point.lng)
    })
  }
  map.setView([lat, lng], zoom)
}

function previewSuggestion(suggestion: Suggestion) {
  if (!Number.isFinite(suggestion.lat) || !Number.isFinite(suggestion.lng)) return
  if (suggestion.lat === 0 && suggestion.lng === 0) return
  map?.setView([suggestion.lat, suggestion.lng], 14)
}

function setPickedLocation(lat: number, lng: number, label = query.value.trim(), city = "") {
  if (!Number.isFinite(lat) || !Number.isFinite(lng) || Math.abs(lat) > 90 || Math.abs(lng) > 180) {
    status.value = "Those coordinates aren’t valid. Enter latitude, longitude in decimal degrees."
    return
  }
  const coordinates = `${lat.toFixed(6)}, ${lng.toFixed(6)}`
  const address = label || coordinates
  confirmed.value = true
  selectedCoordinates.value = coordinates
  coordinateInput.value = coordinates
  status.value = label
    ? "Location pinned. The typed address will be saved with this exact map pin."
    : "Location pinned. Add a place or address above so the service provider can find it."
  updateMap(lat, lng)
  emit("picked", { address, city, latitude: lat, longitude: lng })
}

function handleMapClick(event: any) {
  const { lat, lng } = event.latlng
  void selectMapLocation(lat, lng)
}

async function reverseGeocode(lat: number, lng: number): Promise<{ address: string; city: string }> {
  const url = `https://nominatim.openstreetmap.org/reverse?format=jsonv2&addressdetails=1&zoom=18&accept-language=en&lat=${lat}&lon=${lng}`
  const response = await fetch(url)
  if (!response.ok) throw new Error(`Reverse geocoding failed (${response.status}).`)
  const result = await response.json()
  const address = result.display_name
  if (!address) throw new Error("No street address was found for this map pin.")
  const parts = result.address ?? {}
  return {
    address,
    city: parts.city || parts.town || parts.village || parts.county || parts.state || "",
  }
}

async function selectMapLocation(lat: number, lng: number) {
  clearTimeout(timer)
  requestId++
  const id = requestId
  suggestions.value = []
  confirmed.value = false
  status.value = "Finding the address for this map pin..."
  updateMap(lat, lng)
  try {
    const result = await reverseGeocode(lat, lng)
    if (id !== requestId) return
    query.value = result.address
    setPickedLocation(lat, lng, result.address, result.city)
    status.value = "Map pin selected and address filled in."
  } catch (error) {
    if (id !== requestId) return
    const coordinates = `${lat.toFixed(6)}, ${lng.toFixed(6)}`
    query.value = coordinates
    setPickedLocation(lat, lng, coordinates)
    status.value = error instanceof Error
      ? `${error.message} The coordinates are selected; you can add a landmark name in the address field.`
      : "Could not look up this pin’s address. The coordinates are selected; add a landmark name if needed."
  }
}

function applyCoordinates() {
  let value = coordinateInput.value.trim()
  try {
    value = decodeURIComponent(value)
  } catch {
    // Keep the original input if it is not valid URI-encoded text.
  }
  const patterns = [
    /@(-?\d{1,2}(?:\.\d+)?),\s*(-?\d{1,3}(?:\.\d+)?)/,
    /!3d(-?\d{1,2}(?:\.\d+)?)!4d(-?\d{1,3}(?:\.\d+)?)/,
    /(?:[?&](?:q|query|ll|destination)=)(-?\d{1,2}(?:\.\d+)?)[,%20]+(-?\d{1,3}(?:\.\d+)?)/i,
    /^\s*(-?\d{1,2}(?:\.\d+)?)\s*,\s*(-?\d{1,3}(?:\.\d+)?)\s*$/,
  ]
  const match = patterns.map((pattern) => value.match(pattern)).find(Boolean)
  if (!match) {
    confirmed.value = false
    status.value = "Paste a Google Maps link with coordinates or enter latitude, longitude (for example, 30.19438, 71.53746)."
    return
  }
  setPickedLocation(Number(match[1]), Number(match[2]))
}

async function googlePlaces(q: string): Promise<Suggestion[]> {
  const apiKey = config.public.googleMapsApiKey
  if (!apiKey) return []

  const response = await fetch("https://places.googleapis.com/v1/places:autocomplete", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Goog-Api-Key": apiKey,
      "X-Goog-FieldMask": "suggestions.placePrediction.placeId,suggestions.placePrediction.text",
    },
    body: JSON.stringify({
      input: q,
      includedRegionCodes: ["pk"],
      languageCode: "en",
      locationBias: {
        circle: {
          center: { latitude: BIAS_LAT, longitude: BIAS_LON },
          radius: 500000,
        },
      },
    }),
  })
  if (!response.ok) {
    throw new Error(`Google Places search failed (${response.status})`)
  }

  const data = await response.json()
  return (data.suggestions ?? [])
    .map((suggestion: any) => suggestion.placePrediction)
    .filter((prediction: any) => prediction?.placeId && prediction?.text?.text)
    .map((prediction: any) => ({
      label: prediction.text.text,
      city: "",
      lat: 0,
      lng: 0,
      placeId: prediction.placeId,
    }))
}

async function googlePlaceDetails(placeId: string): Promise<Suggestion> {
  const apiKey = config.public.googleMapsApiKey
  const response = await fetch(`https://places.googleapis.com/v1/places/${encodeURIComponent(placeId)}?languageCode=en`, {
    headers: {
      "X-Goog-Api-Key": apiKey,
      "X-Goog-FieldMask": "location,displayName,formattedAddress,addressComponents",
    },
  })
  if (!response.ok) {
    throw new Error(`Google Places details failed (${response.status})`)
  }

  const place = await response.json()
  const location = place.location
  if (!Number.isFinite(location?.latitude) || !Number.isFinite(location?.longitude)) {
    throw new Error("Google Places did not return coordinates for this result.")
  }
  const cityComponent = (place.addressComponents ?? []).find((component: any) =>
    component.types?.some((type: string) =>
      ["locality", "postal_town", "administrative_area_level_2"].includes(type)
    )
  )

  return {
    label: place.formattedAddress || place.displayName?.text || "",
    city: cityComponent?.longText || "",
    lat: location.latitude,
    lng: location.longitude,
  }
}

async function photon(q: string): Promise<Suggestion[]> {
  const url = `https://photon.komoot.io/api/?q=${encodeURIComponent(q)}&limit=8&lang=en&lat=${BIAS_LAT}&lon=${BIAS_LON}&location_bias_scale=1.0`
  const r = await fetch(url)
  if (!r.ok) throw new Error("photon")
  const data = await r.json()
  return normalizeResults(
    (data.features ?? []).map((f: any) => {
      const p = f.properties ?? {}
      const street = [p.housenumber, p.street].filter(Boolean).join(" ")
      const city = p.city || p.town || p.village || p.county || p.state || ""
      const parts = [p.name, street, p.district, city, p.state, p.country].filter(Boolean)
      const label = parts.filter((v: string, i: number) => parts.indexOf(v) === i).join(", ")
      return { label, city, lat: Number(f.geometry.coordinates[1]), lng: Number(f.geometry.coordinates[0]) }
    })
  )
}

async function nominatim(q: string): Promise<Suggestion[]> {
  const url = `https://nominatim.openstreetmap.org/search?format=jsonv2&addressdetails=1&limit=8&countrycodes=pk&accept-language=en&namedetails=1&q=${encodeURIComponent(q)}`
  const r = await fetch(url)
  if (!r.ok) throw new Error("nominatim")
  const list = await r.json()
  return normalizeResults(
    list.map((d: any) => {
      const a = d.address ?? {}
      return {
        label: d.display_name,
        city: a.city || a.town || a.village || a.county || a.state || "",
        lat: Number(d.lat),
        lng: Number(d.lon),
      }
    })
  )
}

async function find(q: string): Promise<Suggestion[]> {
  let googleResults: Suggestion[] = []
  if (config.public.googleMapsApiKey) {
    googleResults = await googlePlaces(q)
  }

  let list: Suggestion[] = []
  try {
    list = await photon(q)
  } catch {
    // Fallback to Nominatim when Photon rejects or is incomplete.
  }
  if (!list.length) {
    try {
      list = await nominatim(q)
    } catch {
      // Ignore geocoder failures. The user can still type a full address manually.
    }
  }

  const nearbyQuery = q
    .replace(/\b(?:govt|government|higher|secondary|school|college|university|hospital|no\.?)\b/gi, " ")
    .replace(/\b\d+\b/g, " ")
    .replace(/\s+/g, " ")
    .trim()
  if (nearbyQuery && nearbyQuery.toLowerCase() !== q.toLowerCase()) {
    let nearbyResults: Suggestion[] = []
    try {
      nearbyResults = await photon(nearbyQuery)
    } catch {
      // Try the backup geocoder for the shorter locality query.
    }
    if (!nearbyResults.length) {
      try {
        nearbyResults = await nominatim(nearbyQuery)
      } catch {
        // Keep results already found by Google Places or the original query.
      }
    }
    list = normalizeResults([...list, ...nearbyResults])
  }

  const seen = new Set(googleResults.map((result) => result.placeId).filter(Boolean))
  return [
    ...googleResults,
    ...list.filter((result) => {
      const key = `${result.label}|${result.lat.toFixed(6)}|${result.lng.toFixed(6)}`
      if (seen.has(key)) return false
      seen.add(key)
      return true
    }),
  ]
}

function onInput() {
  clearTimeout(timer)
  requestId++
  confirmed.value = false
  selectedCoordinates.value = ""
  coordinateInput.value = ""
  if (marker) {
    marker.remove()
    marker = null
  }
  emit("cleared")
  const q = query.value.trim()
  if (q.length < 3) {
    suggestions.value = []
    return
  }
  timer = setTimeout(async () => {
    const id = ++requestId
    status.value = "Searching..."
    try {
      const list = await find(q)
      if (id !== requestId) return
      suggestions.value = list
      const firstLocatedResult = list.find((result) => result.lat !== 0 || result.lng !== 0)
      if (firstLocatedResult) previewSuggestion(firstLocatedResult)
      status.value = list.length
        ? "The map previews a nearby match. Choose a result or click the exact service location."
        : "No match found. Try another area or click the exact location on the map."
    } catch (error) {
      if (id !== requestId) return
      suggestions.value = []
      status.value = error instanceof Error ? error.message : "Location search failed."
    }
  }, 500)
}

function onCoordinatesInput() {
  if (confirmed.value) {
    confirmed.value = false
    selectedCoordinates.value = ""
    if (marker) {
      marker.remove()
      marker = null
    }
    emit("cleared")
  }
}

async function searchNow() {
  clearTimeout(timer)
  const first = suggestions.value[0]
  if (first) return choose(first)
  const q = query.value.trim()
  if (!q) return
  try {
    const list = await find(q)
    const best = list[0]
    if (best) await choose(best)
    else status.value = "Address not found. Add the area or city."
  } catch (error) {
    status.value = error instanceof Error ? error.message : "Location search failed."
  }
}

async function choose(s: Suggestion) {
  clearTimeout(timer)
  requestId++
  if (s.placeId) {
    status.value = "Loading exact place location..."
    try {
      s = await googlePlaceDetails(s.placeId)
    } catch (error) {
      status.value = error instanceof Error ? error.message : "Could not load this place location."
      return
    }
  }
  suggestions.value = []
  query.value = s.label
  setPickedLocation(s.lat, s.lng, s.label, s.city)
  status.value = "Location selected."
}

function useMyLocation() {
  if (!navigator.geolocation) {
    status.value = "Your browser does not support location."
    return
  }
  status.value = "Getting your location..."
  navigator.geolocation.getCurrentPosition(
    async (pos) => {
      const lat = pos.coords.latitude
      const lng = pos.coords.longitude
      let address = `${lat.toFixed(6)}, ${lng.toFixed(6)}`
      let city = ""
      try {
        const result = await reverseGeocode(lat, lng)
        address = result.address
        city = result.city
      } catch {
        status.value = "Could not look up the street address. Using your coordinates instead."
      }
      clearTimeout(timer)
      requestId++
      suggestions.value = []
      query.value = address
      setPickedLocation(lat, lng, address, city)
      status.value = "Location selected."
    },
    () => { status.value = "Location blocked. Allow location in the browser, or type your address." },
    { enableHighAccuracy: true, timeout: 10000 }
  )
}

onMounted(async () => {
  // @ts-ignore Leaflet has no type declarations installed.
  const mod: any = await import("leaflet")
  L = mod.default ?? mod
  markerIcon = L.icon({
    iconUrl: `data:image/svg+xml,${encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="32" height="42" viewBox="0 0 32 42"><path fill="#2563eb" stroke="#fff" stroke-width="2" d="M16 1C7.7 1 1 7.7 1 16c0 11 15 25 15 25s15-14 15-25C31 7.7 24.3 1 16 1z"/><circle cx="16" cy="16" r="5" fill="#fff"/></svg>')}`,
    iconSize: [32, 42],
    iconAnchor: [16, 42],
  })
  map = L.map(mapElement.value, { scrollWheelZoom: false }).setView([BIAS_LAT, BIAS_LON], 11)
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "&copy; OpenStreetMap contributors",
    maxZoom: 19,
  }).addTo(map)
  map.on("click", handleMapClick)
  setTimeout(() => map.invalidateSize(), 0)
})
</script>

<style scoped>
.picker { position: relative; }
.search-row { display: flex; gap: 8px; }
.search-row input { flex: 1; padding: 9px 12px; border: 1px solid #ccc; border-radius: 6px; }
.search-row button { padding: 9px 14px; border: 0; border-radius: 6px; background: #2563eb; color: #fff; cursor: pointer; white-space: nowrap; }
.suggestions { position: relative; z-index: 1; margin: 4px 0 0; padding: 0; list-style: none; background: #fff; color: #111; border: 1px solid #ccc; border-radius: 6px; box-shadow: 0 6px 16px rgba(0,0,0,.15); max-height: 220px; overflow-y: auto; }
.suggestions li { padding: 9px 12px; font-size: 14px; cursor: pointer; border-bottom: 1px solid #eee; }
.suggestions li:last-child { border-bottom: 0; }
.suggestions li:hover { background: #eff6ff; }
.map-panel { margin-top: 16px; overflow: hidden; border: 1px solid #dbe3ee; border-radius: 10px; background: #f8fafc; }
.map-heading { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 12px 14px; }
.map-heading h3 { margin: 0; color: #142b50; font-size: 15px; }
.map-heading p { margin: 4px 0 0; color: #64748b; font-size: 12px; }
.live-badge { display: inline-flex; align-items: center; gap: 6px; flex: none; color: #166534; font-size: 11px; font-weight: 700; }
.live-badge span { width: 8px; height: 8px; border-radius: 50%; background: #22c55e; box-shadow: 0 0 0 3px rgb(34 197 94 / 15%); }
.location-map { height: 340px; width: 100%; border-block: 1px solid #dbe3ee; z-index: 0; }
.map-attribution { margin: 0; padding: 5px 10px; color: #64748b; text-align: right; font-size: 10px; }
.coordinates-row { display: flex; flex-direction: column; gap: 6px; margin-top: 12px; }
.coordinates-row label { font-size: 13px; font-weight: 600; }
.selected-coordinates { margin: 4px 0 0; font-size: 12px; color: #4b5563; }
.status { font-size: 13px; margin-top: 8px; }
.status.ok { color: #15803d; }
@media (max-width: 540px) {
  .search-row { flex-direction: column; }
  .search-row button { width: 100%; }
  .map-heading { align-items: flex-start; }
  .location-map { height: 280px; }
}
</style>

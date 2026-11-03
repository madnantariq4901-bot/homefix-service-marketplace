<template>
  <div class="viewer">
    <div ref="mapEl" class="map"></div>
    <p v-if="lat == null || lng == null" class="note">This provider has not shared a location yet.</p>
    <a v-else class="dir" target="_blank" rel="noopener"
       :href="`https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}`">Get directions</a>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from "vue"
// @ts-ignore Leaflet's CSS file has no TypeScript declaration.
import "leaflet/dist/leaflet.css"

const props = defineProps<{ lat?: number | null; lng?: number | null; name?: string }>()

const mapEl = ref<HTMLElement | null>(null)
let L: any, map: any, marker: any, markerIcon: any

function draw() {
  if (!map || props.lat == null || props.lng == null) return
  if (marker) marker.setLatLng([props.lat, props.lng])
  else marker = L.marker([props.lat, props.lng], { icon: markerIcon }).addTo(map)
  if (props.name) marker.bindPopup(props.name)
  map.setView([props.lat, props.lng], 15)
  setTimeout(() => map.invalidateSize(), 100)
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
  map = L.map(mapEl.value!, { scrollWheelZoom: false }).setView([30.1575, 71.5249], 11)
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "&copy; OpenStreetMap contributors",
    maxZoom: 19,
  }).addTo(map)
  draw()
})

watch(() => [props.lat, props.lng], draw)
</script>

<style scoped>
.map { height: 240px; border: 1px solid #ccc; border-radius: 6px; }
.note { font-size: 13px; margin-top: 8px; }
.dir { display: inline-block; margin-top: 8px; font-size: 14px; color: #2563eb; text-decoration: underline; }
</style>

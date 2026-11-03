<script setup lang="ts">
const providersStore = useProvidersStore()
const idFront = ref<File | null>(null)
const idBack = ref<File | null>(null)
const selfie = ref<File | null>(null)
const video = ref<HTMLVideoElement | null>(null)
const cameraActive = ref(false)
const cameraError = ref("")
let mediaStream: MediaStream | null = null

function stopCamera() {
  mediaStream?.getTracks().forEach(track => track.stop())
  mediaStream = null
  cameraActive.value = false
}

async function startCamera() {
  cameraError.value = ""
  if (!navigator.mediaDevices?.getUserMedia) {
    cameraError.value = "Live camera capture is unavailable in this browser. Use a secure connection and allow camera access."
    return
  }

  try {
    mediaStream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: { ideal: "user" } },
      audio: false,
    })
    cameraActive.value = true
    await nextTick()
    if (video.value) {
      video.value.srcObject = mediaStream
      await video.value.play()
    }
  } catch {
    stopCamera()
    cameraError.value = "Unable to open the front camera. Allow camera access and try again."
  }
}

function captureSelfie() {
  const currentVideo = video.value
  if (!currentVideo || !currentVideo.videoWidth || !currentVideo.videoHeight) {
    cameraError.value = "Wait for the camera image to appear, then capture your selfie."
    return
  }

  const canvas = document.createElement("canvas")
  canvas.width = currentVideo.videoWidth
  canvas.height = currentVideo.videoHeight
  const context = canvas.getContext("2d")
  if (!context) {
    cameraError.value = "Unable to capture a selfie from the camera."
    return
  }
  context.drawImage(currentVideo, 0, 0)
  canvas.toBlob((image) => {
    if (!image) {
      cameraError.value = "Unable to capture a selfie from the camera."
      return
    }
    selfie.value = new File([image], "provider-selfie.jpg", { type: "image/jpeg" })
    cameraError.value = ""
    stopCamera()
  }, "image/jpeg", 0.9)
}

async function submitIdentity() {
  if (!idFront.value || !idBack.value || !selfie.value) return

  const form = new FormData()
  form.append("id_front", idFront.value)
  form.append("id_back", idBack.value)
  form.append("selfie", selfie.value)
  try {
    await providersStore.uploadIdentityDocuments(form)
  } catch {
    // The store retains the API error for display.
  }
}

onBeforeUnmount(stopCamera)
</script>

<template>
  <form class="identity-form" @submit.prevent="submitIdentity">
    <p>Submit clear images of both sides of your government ID and take a live selfie. These files are stored privately and are never shown on your public profile.</p>
    <label>
      Government ID — front
      <input
        type="file"
        accept="image/jpeg,image/png"
        required
        :disabled="providersStore.loading"
        @change="idFront = ($event.target as HTMLInputElement).files?.[0] ?? null"
      />
    </label>
    <label>
      Government ID — back
      <input
        type="file"
        accept="image/jpeg,image/png"
        required
        :disabled="providersStore.loading"
        @change="idBack = ($event.target as HTMLInputElement).files?.[0] ?? null"
      />
    </label>

    <div class="selfie">
      <strong>Live selfie</strong>
      <video v-if="cameraActive" ref="video" autoplay playsinline muted />
      <div class="camera-actions">
        <button v-if="!cameraActive && !selfie" type="button" :disabled="providersStore.loading" @click="startCamera">Open front camera</button>
        <button v-if="cameraActive" type="button" @click="captureSelfie">Capture selfie</button>
        <button v-if="selfie && !cameraActive" type="button" class="secondary" @click="startCamera">Retake selfie</button>
        <span v-if="selfie">Selfie captured</span>
      </div>
    </div>

    <AppAlert v-if="cameraError" type="error">{{ cameraError }}</AppAlert>
    <AppAlert v-if="providersStore.error" type="error">{{ providersStore.error }}</AppAlert>
    <button type="submit" :disabled="providersStore.loading || !idFront || !idBack || !selfie">
      {{ providersStore.loading ? "Submitting..." : "Submit identity documents" }}
    </button>
  </form>
</template>

<style scoped>
.identity-form { display: grid; gap: 14px; max-width: 600px; }
.identity-form > p { margin: 0; color: var(--color-muted); }
label { display: grid; gap: 6px; font-size: 14px; font-weight: 600; }
.selfie { display: grid; gap: 10px; }
video { width: min(100%, 420px); max-height: 320px; background: #111827; border-radius: 10px; }
.camera-actions { display: flex; flex-wrap: wrap; align-items: center; gap: 10px; }
.secondary { color: var(--color-text); background: var(--color-surface); border: 1px solid var(--color-border); }
</style>

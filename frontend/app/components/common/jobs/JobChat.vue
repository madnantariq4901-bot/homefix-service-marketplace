<script setup lang="ts">
import { MapPin, Send } from "lucide-vue-next"
import { jobMessagesService } from "~/services/job-messages.service"
import type { JobMessage } from "~/types/jobMessage"

const props = defineProps<{ jobId: number; partnerName: string }>()
const draft = ref("")
const messages = ref<JobMessage[]>([])
const loading = ref(true)
const sending = ref(false)
const error = ref("")
const messageList = ref<HTMLElement | null>(null)
const { messages: realtimeEvents, connected, connect } = useWebSocket()

function appendMessage(message: JobMessage) {
  if (messages.value.some(item => item.id === message.id)) return
  messages.value.push(message)
  messages.value.sort((first, second) => first.id - second.id)
  nextTick(() => messageList.value?.scrollTo({ top: messageList.value.scrollHeight, behavior: "smooth" }))
}

function handleRealtimeEvent(event: unknown) {
  if (!event || typeof event !== "object" || !("type" in event) || event.type !== "chat_message") return
  if (!("message" in event) || !event.message || typeof event.message !== "object") return
  appendMessage(event.message as JobMessage)
}

watch(() => realtimeEvents.value.length, () => {
  handleRealtimeEvent(realtimeEvents.value.at(-1))
})

async function loadMessages() {
  loading.value = true
  error.value = ""
  connect(props.jobId)
  try {
    for (const message of await jobMessagesService.list(props.jobId)) appendMessage(message)
  } catch (err: any) {
    error.value = err?.data?.detail || "Unable to load this conversation."
  } finally {
    loading.value = false
  }
}

async function sendText() {
  const body = draft.value.trim()
  if (!body || sending.value) return
  sending.value = true
  error.value = ""
  try {
    appendMessage(await jobMessagesService.send(props.jobId, { body }))
    draft.value = ""
  } catch (err: any) {
    error.value = err?.data?.detail || "Message could not be sent."
  } finally {
    sending.value = false
  }
}

async function shareLocation() {
  if (!navigator.geolocation || sending.value) {
    error.value = "Location sharing is not available in this browser."
    return
  }

  sending.value = true
  error.value = ""
  try {
    const position = await new Promise<GeolocationPosition>((resolve, reject) => {
      navigator.geolocation.getCurrentPosition(resolve, reject, {
        enableHighAccuracy: false,
        maximumAge: 0,
        timeout: 15000,
      })
    })
    appendMessage(await jobMessagesService.send(props.jobId, {
      latitude: position.coords.latitude,
      longitude: position.coords.longitude,
    }))
  } catch (err: any) {
    error.value = err?.code === 1
      ? "Location permission was denied. No location was shared."
      : err?.data?.detail || "Could not get your location. No location was shared."
  } finally {
    sending.value = false
  }
}

function messageTime(value: string) {
  return new Date(value).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })
}

onMounted(loadMessages)
</script>

<template>
  <aside class="job-chat" aria-label="Job chat">
    <header class="chat-header">
      <div>
        <p class="chat-kicker">Job conversation</p>
        <h2>{{ partnerName }}</h2>
      </div>
      <span class="connection" :class="{ online: connected }" :aria-label="connected ? 'Live connection' : 'Connecting'" />
    </header>

    <p class="privacy-note">Only you and the other job participant can see these messages.</p>
    <p v-if="error" class="chat-error" role="alert">{{ error }}</p>

    <div ref="messageList" class="message-list" aria-live="polite" aria-relevant="additions text">
      <p v-if="loading" class="empty-chat">Loading conversation...</p>
      <p v-else-if="!messages.length" class="empty-chat">No messages yet. Start the conversation.</p>
      <article v-for="message in messages" :key="message.id" class="message" :class="{ location: message.latitude !== null }">
        <div class="message-meta"><strong>{{ message.sender_name }}</strong><time>{{ messageTime(message.created_at) }}</time></div>
        <p v-if="message.body" class="message-body">{{ message.body }}</p>
        <div v-else class="shared-location">
          <MapPin :size="17" aria-hidden="true" />
          <span>Shared their location</span>
          <a
            :href="`https://www.google.com/maps/search/?api=1&query=${message.latitude},${message.longitude}`"
            target="_blank"
            rel="noopener noreferrer"
          >Open map</a>
        </div>
      </article>
    </div>

    <form class="composer" @submit.prevent="sendText">
      <label class="sr-only" for="job-chat-message">Message</label>
      <textarea id="job-chat-message" v-model="draft" rows="2" maxlength="2000" placeholder="Write a message..." />
      <div class="composer-actions">
        <button class="location-button" type="button" :disabled="sending" @click="shareLocation">
          <MapPin :size="16" aria-hidden="true" /> Share my location
        </button>
        <button class="send-button" type="submit" :disabled="sending || !draft.trim()" aria-label="Send message" title="Send message">
          <Send :size="16" aria-hidden="true" />
        </button>
      </div>
      <p class="location-disclosure">Your location is sent once, only after you choose Share and allow browser access.</p>
    </form>
  </aside>
</template>

<style scoped>
.job-chat { position: sticky; top: 84px; display: flex; flex-direction: column; min-width: 0; height: min(700px, calc(100dvh - 110px)); max-height: 700px; overflow: hidden; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: 10px; }
.chat-header { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 17px 16px 13px; border-bottom: 1px solid var(--color-border); }
.chat-kicker { margin: 0 0 3px; color: var(--color-primary); font-size: 11px; font-weight: 700; text-transform: uppercase; }
.chat-header h2 { overflow: hidden; margin: 0; font-size: 17px; text-overflow: ellipsis; white-space: nowrap; }
.connection { flex: 0 0 9px; width: 9px; height: 9px; border-radius: 50%; background: #c4cbd3; }
.connection.online { background: #219653; box-shadow: 0 0 0 3px #21965320; }
.privacy-note { margin: 0; padding: 9px 14px; color: var(--color-muted); background: var(--color-page); font-size: 11px; line-height: 1.4; }
.chat-error { margin: 0; padding: 8px 13px; color: #a32118; background: #fff1f0; font-size: 12px; }
.message-list { display: flex; flex: 1; min-height: 120px; flex-direction: column; gap: 12px; overflow-y: auto; padding: 14px 12px; }
.empty-chat { margin: auto; color: var(--color-muted); font-size: 13px; text-align: center; }
.message { max-width: 92%; align-self: flex-start; padding: 9px 10px; background: var(--color-page); border: 1px solid var(--color-border); border-radius: 8px; overflow-wrap: anywhere; }
.message-meta { display: flex; justify-content: space-between; gap: 12px; color: var(--color-muted); font-size: 10px; }
.message-meta strong { color: var(--color-text); font-size: 11px; }
.message-body { margin: 5px 0 0; color: var(--color-text); font-size: 13px; line-height: 1.45; white-space: pre-wrap; }
.shared-location { display: flex; flex-wrap: wrap; align-items: center; gap: 7px; margin-top: 5px; font-size: 12px; }
.shared-location a { color: var(--color-primary); font-weight: 700; }
.composer { display: grid; gap: 8px; max-width: none; padding: 11px; border-top: 1px solid var(--color-border); }
.composer textarea { width: 100%; min-height: 54px; resize: vertical; font-size: 13px; }
.composer-actions { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.location-button, .send-button { display: inline-flex; align-items: center; justify-content: center; gap: 6px; min-height: 34px; padding: 6px 9px; font-size: 12px; }
.location-button { color: var(--color-primary); background: transparent; border: 1px solid var(--color-border); box-shadow: none; }
.location-button:hover:not(:disabled) { background: var(--color-page); box-shadow: none; transform: none; }
.send-button { width: 36px; min-width: 36px; padding: 0; }
.location-disclosure { margin: 0; color: var(--color-muted); font-size: 10px; line-height: 1.35; }
.sr-only { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0, 0, 0, 0); white-space: nowrap; }
@media (max-width: 760px) {
  .job-chat { position: static; height: 520px; max-height: 70dvh; }
}
</style>
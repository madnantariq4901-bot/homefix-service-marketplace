export function useWebSocket() {
  const socket = ref<WebSocket | null>(null)
  const messages = ref<unknown[]>([])
  const connected = ref(false)

  function connect(jobId: number) {
    if (import.meta.server || !Number.isInteger(jobId) || jobId < 1) return
    disconnect()
    const config = useRuntimeConfig()
    const token = useCookie<string | null>("access_token").value
    if (!token) return

    const apiUrl = String(config.public.apiBaseUrl)
      .replace(/^http:/, "ws:")
      .replace(/^https:/, "wss:")
    const query = new URLSearchParams({ token })
    socket.value = new WebSocket(`${apiUrl}/ws/jobs/${jobId}?${query.toString()}`)

    socket.value.onopen = () => {
      connected.value = true
    }
    socket.value.onmessage = (event) => {
      try {
        messages.value.push(JSON.parse(event.data))
      } catch {
        messages.value.push(event.data)
      }
    }
    socket.value.onclose = () => {
      connected.value = false
      socket.value = null
    }
  }

  function disconnect() {
    if (socket.value) {
      socket.value.onclose = null
      socket.value.close()
    }
    socket.value = null
    connected.value = false
  }

  onUnmounted(disconnect)

  return { socket, messages, connected, connect, disconnect }
}

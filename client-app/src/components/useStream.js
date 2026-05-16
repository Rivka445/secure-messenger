import { useEffect, useRef } from 'react'

export default function useStream(onMessage) {
  const onMessageRef = useRef(onMessage)
  onMessageRef.current = onMessage

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (!token) {
      console.warn('[SSE] No token, skipping stream connection')
      return
    }

    const controller = new AbortController()
    let active = true

    async function connect() {
      console.log('[SSE] Connecting...')
      try {
        const res = await fetch('http://localhost:8000/stream', {
          headers: { Authorization: `Bearer ${token}` },
          signal: controller.signal,
        })
        console.log('[SSE] Connected, status:', res.status)
        if (!res.ok || !res.body) {
          console.error('[SSE] Bad response:', res.status)
          return
        }
        const reader = res.body.getReader()
        const decoder = new TextDecoder()
        let buffer = ''
        while (active) {
          const { done, value } = await reader.read()
          if (done) break
          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split('\n')
          buffer = lines.pop()
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const parsed = JSON.parse(line.slice(6))
                console.log('[SSE] Message received:', parsed)
                onMessageRef.current(parsed)
              } catch (e) {
                console.error('[SSE] Parse error:', e)
              }
            }
          }
        }
      } catch (e) {
        if (e.name !== 'AbortError') console.error('[SSE] Error:', e)
      }
    }

    connect()
    return () => {
      active = false
      controller.abort()
    }
  }, [])
}

import { useEffect, useRef, useCallback, useState } from 'react'
import { useStore } from '../store'

export function useWebSocket() {
  const ws = useRef<WebSocket | null>(null)
  const reconnectTimeout = useRef<NodeJS.Timeout | null>(null)
  const { setAgents, updateAgentStatus, setConnected } = useStore()
  const [retryCount, setRetryCount] = useState(0)

  const connect = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) return

    try {
      const wsUrl = `ws://localhost:8000/ws`
      ws.current = new WebSocket(wsUrl)

      ws.current.onopen = () => {
        console.log('WebSocket connected')
        setConnected(true)
        setRetryCount(0)
      }

      ws.current.onclose = () => {
        console.log('WebSocket disconnected')
        setConnected(false)
        
        // Reconnect with backoff
        const delay = Math.min(1000 * Math.pow(2, retryCount), 10000)
        reconnectTimeout.current = setTimeout(() => {
          setRetryCount(r => r + 1)
          connect()
        }, delay)
      }

      ws.current.onerror = (error) => {
        console.log('WebSocket error:', error)
      }

      ws.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          console.log('WebSocket message:', data)
          
          if (data.event === 'connected' && data.data?.agents) {
            setAgents(data.data.agents)
          } else if (data.event === 'agent_status') {
            updateAgentStatus(data.agent, data.data.status)
          } else if (data.event === 'task_started') {
            updateAgentStatus(data.agent, 'walking')
          } else if (data.event === 'task_completed') {
            // Brief reporting state, then idle
            updateAgentStatus(data.agent, 'reporting')
            setTimeout(() => updateAgentStatus(data.agent, 'idle'), 2000)
          }
        } catch (e) {
          console.error('WebSocket message error:', e)
        }
      }
    } catch (e) {
      console.error('WebSocket connection error:', e)
      setConnected(false)
    }
  }, [setAgents, updateAgentStatus, setConnected, retryCount])

  const send = useCallback((command: string, agent?: string, task?: string) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ command, agent, task }))
    }
  }, [])

  useEffect(() => {
    // Initial connect
    connect()
    
    // Also fetch agents via HTTP as fallback
    fetch('http://localhost:8000/agents')
      .then(res => res.json())
      .then(agents => {
        if (Array.isArray(agents)) {
          setAgents(agents)
        }
      })
      .catch(e => console.log('HTTP fallback failed:', e))

    return () => {
      if (reconnectTimeout.current) {
        clearTimeout(reconnectTimeout.current)
      }
      ws.current?.close()
    }
  }, [connect, setAgents])

  return { send }
}

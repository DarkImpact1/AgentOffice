import { Canvas } from '@react-three/fiber'
import { Suspense, useState } from 'react'
import { Office } from './components/Office'
import { TaskPanel } from './components/TaskPanel'
import { useWebSocket, API_URL } from './hooks/useWebSocket'
import { useStore, Agent } from './store'

function LoadingFallback() {
  return (
    <mesh>
      <boxGeometry args={[1, 1, 1]} />
      <meshStandardMaterial color="gray" />
    </mesh>
  )
}

interface ChatModalProps {
  agent: Agent
  onClose: () => void
  onSubmit: (task: string) => void
}

function ChatModal({ agent, onClose, onSubmit }: ChatModalProps) {
  const [input, setInput] = useState('')
  const [status, setStatus] = useState<'asking' | 'working' | 'done'>('asking')
  const [result, setResult] = useState('')

  const handleSubmit = async () => {
    if (!input.trim()) return
    setStatus('working')
    
    try {
      const response = await fetch(`${API_URL}/agents/${agent.name}/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task: input })
      })
      const data = await response.json()
      setResult(data.message || 'Task completed!')
      setStatus('done')
      onSubmit(input)
    } catch (e) {
      setResult('Sorry sir, something went wrong!')
      setStatus('done')
    }
  }

  const suggestions: Record<string, string[]> = {
    email: ['Check my inbox', 'Find urgent emails', 'Look for meeting invites'],
    tab_monitor: ['Check all platforms', 'Check Outlier status', 'Any new tasks available?'],
    freelance_hunter: ['Find Python jobs', 'Search React projects', 'Look for DevOps gigs'],
    status_tracker: ['Give me daily report', 'Show productivity stats', 'Weekly summary'],
  }

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'rgba(0,0,0,0.8)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
    }}>
      <div style={{
        background: '#1a1a2e',
        borderRadius: 16,
        padding: 24,
        width: 450,
        maxWidth: '90%',
        border: `2px solid ${agent.color}`,
      }}>
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20 }}>
          <span style={{ fontSize: 40 }}>{agent.avatar}</span>
          <div>
            <div style={{ color: agent.color, fontSize: 18, fontWeight: 'bold' }}>
              {agent.name.replace('_', ' ').toUpperCase()}
            </div>
            <div style={{ color: '#a0aec0', fontSize: 13 }}>{agent.description}</div>
          </div>
          <button
            onClick={onClose}
            style={{
              marginLeft: 'auto',
              background: 'none',
              border: 'none',
              color: '#a0aec0',
              fontSize: 24,
              cursor: 'pointer',
            }}
          >
            ×
          </button>
        </div>

        {/* Chat area */}
        <div style={{
          background: '#0f0f1a',
          borderRadius: 8,
          padding: 16,
          marginBottom: 16,
          minHeight: 120,
        }}>
          {status === 'asking' && (
            <div style={{ color: '#ffffff' }}>
              <div style={{ marginBottom: 12 }}>
                <span style={{ color: agent.color }}>Agent:</span> How may I help you, sir? 🙏
              </div>
              <div style={{ color: '#718096', fontSize: 12, marginTop: 8 }}>
                Quick suggestions:
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 8 }}>
                {(suggestions[agent.name] || []).map((s, i) => (
                  <button
                    key={i}
                    onClick={() => setInput(s)}
                    style={{
                      background: '#2d3748',
                      border: 'none',
                      borderRadius: 4,
                      padding: '6px 12px',
                      color: '#a0aec0',
                      fontSize: 12,
                      cursor: 'pointer',
                    }}
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}
          
          {status === 'working' && (
            <div style={{ color: '#ffffff' }}>
              <div><span style={{ color: '#f59e0b' }}>You:</span> {input}</div>
              <div style={{ marginTop: 12, color: agent.color }}>
                <span className="loading">Working on it...</span> ⏳
              </div>
            </div>
          )}
          
          {status === 'done' && (
            <div style={{ color: '#ffffff' }}>
              <div><span style={{ color: '#f59e0b' }}>You:</span> {input}</div>
              <div style={{ marginTop: 12 }}>
                <span style={{ color: agent.color }}>Agent:</span>
                <div style={{ 
                  marginTop: 8, 
                  whiteSpace: 'pre-wrap',
                  background: '#1a1a2e',
                  padding: 12,
                  borderRadius: 8,
                  fontSize: 13,
                  maxHeight: 200,
                  overflow: 'auto',
                }}>
                  {result}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Input area */}
        {status === 'asking' && (
          <div style={{ display: 'flex', gap: 8 }}>
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
              placeholder="Type your order, sir..."
              style={{
                flex: 1,
                background: '#2d3748',
                border: 'none',
                borderRadius: 8,
                padding: '12px 16px',
                color: 'white',
                fontSize: 14,
                outline: 'none',
              }}
              autoFocus
            />
            <button
              onClick={handleSubmit}
              style={{
                background: agent.color,
                border: 'none',
                borderRadius: 8,
                padding: '12px 20px',
                color: 'white',
                fontWeight: 'bold',
                cursor: 'pointer',
              }}
            >
              Send
            </button>
          </div>
        )}

        {status === 'done' && (
          <div style={{ display: 'flex', gap: 8 }}>
            <button
              onClick={() => {
                setStatus('asking')
                setInput('')
                setResult('')
              }}
              style={{
                flex: 1,
                background: '#2d3748',
                border: 'none',
                borderRadius: 8,
                padding: '12px 16px',
                color: 'white',
                cursor: 'pointer',
              }}
            >
              Ask Again
            </button>
            <button
              onClick={onClose}
              style={{
                flex: 1,
                background: agent.color,
                border: 'none',
                borderRadius: 8,
                padding: '12px 16px',
                color: 'white',
                fontWeight: 'bold',
                cursor: 'pointer',
              }}
            >
              Dismiss
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

function App() {
  const { send } = useWebSocket()
  const { connected, agents, updateAgentStatus } = useStore()
  const [activeAgent, setActiveAgent] = useState<Agent | null>(null)

  const handleAgentClick = (name: string) => {
    const agent = agents.find(a => a.name === name)
    if (!agent) return
    
    console.log('Agent clicked:', name)
    updateAgentStatus(name, 'walking')
    
    // Show chat modal after agent walks
    setTimeout(() => {
      updateAgentStatus(name, 'working')
      setActiveAgent(agent)
    }, 1500)
  }

  const handleChatClose = () => {
    if (activeAgent) {
      updateAgentStatus(activeAgent.name, 'reporting')
      setTimeout(() => updateAgentStatus(activeAgent.name, 'idle'), 1500)
    }
    setActiveAgent(null)
  }

  const handleChatSubmit = (task: string) => {
    console.log('Task submitted:', task)
  }

  return (
    <div style={{ display: 'flex', width: '100%', height: '100%' }}>
      <div style={{ flex: 1, position: 'relative' }}>
        <Canvas 
          shadows 
          camera={{ position: [12, 12, 12], fov: 50 }}
          style={{ background: '#0a0a12' }}
        >
          <Suspense fallback={<LoadingFallback />}>
            <Office onAgentClick={handleAgentClick} />
          </Suspense>
        </Canvas>
        
        {/* Connection status */}
        <div
          style={{
            position: 'absolute',
            top: 16,
            left: 16,
            padding: '8px 16px',
            background: connected ? '#10b981' : '#ef4444',
            color: 'white',
            borderRadius: 8,
            fontSize: 14,
            fontFamily: 'system-ui, sans-serif',
          }}
        >
          {connected ? '🟢 Connected' : '🔴 Reconnecting...'}
        </div>
        
        {/* Instructions */}
        <div
          style={{
            position: 'absolute',
            bottom: 16,
            left: 16,
            padding: '12px 16px',
            background: 'rgba(0,0,0,0.7)',
            color: 'white',
            borderRadius: 8,
            fontSize: 12,
            fontFamily: 'system-ui, sans-serif',
          }}
        >
          👆 Click on an agent to summon them and give orders
        </div>
      </div>
      
      <TaskPanel />
      
      {/* Chat Modal */}
      {activeAgent && (
        <ChatModal
          agent={activeAgent}
          onClose={handleChatClose}
          onSubmit={handleChatSubmit}
        />
      )}
    </div>
  )
}

export default App

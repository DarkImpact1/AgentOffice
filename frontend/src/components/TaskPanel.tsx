import { useState, useEffect } from 'react'
import { useStore, Task, Application } from '../store'

const styles = {
  panel: {
    width: 380,
    height: '100%',
    background: '#1a1a2e',
    borderLeft: '1px solid #2d3748',
    display: 'flex',
    flexDirection: 'column' as const,
    color: 'white',
  },
  header: {
    padding: 16,
    borderBottom: '1px solid #2d3748',
  },
  tabs: {
    display: 'flex',
    gap: 8,
    marginTop: 12,
  },
  tab: (active: boolean) => ({
    padding: '8px 16px',
    background: active ? '#4c51bf' : '#2d3748',
    border: 'none',
    borderRadius: 8,
    color: 'white',
    cursor: 'pointer',
    fontSize: 14,
  }),
  content: {
    flex: 1,
    overflow: 'auto',
    padding: 16,
  },
  card: {
    background: '#2d3748',
    borderRadius: 8,
    padding: 16,
    marginBottom: 12,
  },
  cardTitle: {
    fontSize: 14,
    fontWeight: 600,
    marginBottom: 8,
  },
  cardMeta: {
    fontSize: 12,
    color: '#a0aec0',
    marginBottom: 8,
  },
  badge: (color: string) => ({
    display: 'inline-block',
    padding: '2px 8px',
    background: color,
    borderRadius: 4,
    fontSize: 11,
    marginRight: 8,
  }),
  button: (variant: 'primary' | 'danger' | 'secondary') => ({
    padding: '8px 16px',
    border: 'none',
    borderRadius: 6,
    cursor: 'pointer',
    fontSize: 13,
    marginRight: 8,
    background: variant === 'primary' ? '#10b981' : variant === 'danger' ? '#ef4444' : '#4a5568',
    color: 'white',
  }),
  stats: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: 12,
    marginBottom: 16,
  },
  statCard: {
    background: '#2d3748',
    borderRadius: 8,
    padding: 12,
    textAlign: 'center' as const,
  },
  statValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#10b981',
  },
  statLabel: {
    fontSize: 11,
    color: '#a0aec0',
    marginTop: 4,
  },
}

export function TaskPanel() {
  const [tab, setTab] = useState<'tasks' | 'proposals' | 'agents'>('agents')
  const { agents, tasks, applications, setTasks, setApplications } = useStore()
  const [stats, setStats] = useState({ input_tokens: 0, output_tokens: 0 })

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 10000)
    return () => clearInterval(interval)
  }, [])

  const fetchData = async () => {
    try {
      const [tasksRes, appsRes, statsRes] = await Promise.all([
        fetch('/api/tasks'),
        fetch('/api/tasks/pending-approvals'),
        fetch('/api/stats'),
      ])
      if (tasksRes.ok) setTasks(await tasksRes.json())
      if (appsRes.ok) setApplications(await appsRes.json())
      if (statsRes.ok) {
        const data = await statsRes.json()
        setStats(data.tokens || { input_tokens: 0, output_tokens: 0 })
      }
    } catch (e) {}
  }

  const approveApplication = async (id: number) => {
    await fetch(`/api/tasks/approve/${id}`, { method: 'PATCH' })
    fetchData()
  }

  const updateTaskStatus = async (id: number, status: string) => {
    await fetch(`/api/tasks/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status }),
    })
    fetchData()
  }

  return (
    <div style={styles.panel}>
      <div style={styles.header}>
        <h2 style={{ margin: 0, fontSize: 20 }}>🏢 AgentOffice</h2>
        <div style={styles.tabs}>
          <button style={styles.tab(tab === 'agents')} onClick={() => setTab('agents')}>
            Agents
          </button>
          <button style={styles.tab(tab === 'tasks')} onClick={() => setTab('tasks')}>
            Tasks ({tasks.length})
          </button>
          <button style={styles.tab(tab === 'proposals')} onClick={() => setTab('proposals')}>
            Jobs ({applications.length})
          </button>
        </div>
      </div>

      <div style={styles.content}>
        {tab === 'agents' && (
          <>
            <div style={styles.stats}>
              <div style={styles.statCard}>
                <div style={styles.statValue}>{stats.input_tokens + stats.output_tokens}</div>
                <div style={styles.statLabel}>Total Tokens</div>
              </div>
              <div style={styles.statCard}>
                <div style={styles.statValue}>{agents.filter(a => a.status === 'idle').length}/{agents.length}</div>
                <div style={styles.statLabel}>Agents Idle</div>
              </div>
            </div>
            {agents.map((agent) => (
              <div key={agent.name} style={styles.card}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <span style={{ fontSize: 24 }}>{agent.avatar}</span>
                  <div>
                    <div style={styles.cardTitle}>{agent.name.replace('_', ' ')}</div>
                    <div style={styles.cardMeta}>{agent.description}</div>
                  </div>
                </div>
                <div style={{ marginTop: 8 }}>
                  <span style={styles.badge(
                    agent.status === 'idle' ? '#10b981' :
                    agent.status === 'working' ? '#3b82f6' :
                    agent.status === 'error' ? '#ef4444' : '#f59e0b'
                  )}>
                    {agent.status}
                  </span>
                  {agent.last_run && (
                    <span style={{ fontSize: 11, color: '#718096' }}>
                      Last: {new Date(agent.last_run).toLocaleTimeString()}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </>
        )}

        {tab === 'tasks' && (
          <>
            {tasks.length === 0 ? (
              <div style={{ textAlign: 'center', color: '#718096', padding: 32 }}>
                No tasks yet. Click an agent to get started!
              </div>
            ) : (
              tasks.map((task) => (
                <div key={task.id} style={styles.card}>
                  <div style={styles.cardTitle}>{task.title}</div>
                  <div style={styles.cardMeta}>
                    <span style={styles.badge('#4c51bf')}>{task.source_agent}</span>
                    <span style={styles.badge(
                      task.status === 'completed' ? '#10b981' :
                      task.status === 'pending' ? '#f59e0b' : '#718096'
                    )}>
                      {task.status}
                    </span>
                    {task.due_date && <span>Due: {task.due_date}</span>}
                  </div>
                  <div style={{ fontSize: 12, color: '#a0aec0', marginBottom: 8 }}>
                    {task.description?.slice(0, 100)}
                  </div>
                  {task.status === 'pending' && (
                    <div>
                      <button
                        style={styles.button('primary')}
                        onClick={() => updateTaskStatus(task.id, 'completed')}
                      >
                        ✓ Complete
                      </button>
                      <button
                        style={styles.button('secondary')}
                        onClick={() => updateTaskStatus(task.id, 'dismissed')}
                      >
                        Dismiss
                      </button>
                    </div>
                  )}
                </div>
              ))
            )}
          </>
        )}

        {tab === 'proposals' && (
          <>
            {applications.length === 0 ? (
              <div style={{ textAlign: 'center', color: '#718096', padding: 32 }}>
                No pending proposals. Run the Freelance Hunter to find jobs!
              </div>
            ) : (
              applications.map((app) => (
                <div key={app.id} style={styles.card}>
                  <div style={styles.cardTitle}>{app.job_title}</div>
                  <div style={styles.cardMeta}>
                    <span style={styles.badge('#6366f1')}>{app.platform}</span>
                    <span style={styles.badge('#10b981')}>{app.budget}</span>
                  </div>
                  <div style={{
                    fontSize: 12,
                    color: '#a0aec0',
                    marginBottom: 12,
                    padding: 8,
                    background: '#1a1a2e',
                    borderRadius: 4,
                    maxHeight: 100,
                    overflow: 'auto',
                  }}>
                    {app.proposal}
                  </div>
                  <div>
                    <button
                      style={styles.button('primary')}
                      onClick={() => approveApplication(app.id)}
                    >
                      ✓ Approve & Apply
                    </button>
                    <button style={styles.button('danger')}>
                      ✗ Reject
                    </button>
                    {app.job_url && (
                      <a
                        href={app.job_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{ ...styles.button('secondary'), textDecoration: 'none' }}
                      >
                        View Job
                      </a>
                    )}
                  </div>
                </div>
              ))
            )}
          </>
        )}
      </div>
    </div>
  )
}

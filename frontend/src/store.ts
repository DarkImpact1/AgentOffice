import { create } from 'zustand'

export interface Agent {
  name: string
  description: string
  avatar: string
  color: string
  status: 'idle' | 'walking' | 'working' | 'reporting' | 'error'
  last_run: string | null
}

export interface Task {
  id: number
  title: string
  description: string
  source_agent: string
  status: string
  priority: number
  due_date: string | null
  created_at: string
}

export interface Application {
  id: number
  platform: string
  job_title: string
  job_url: string
  budget: string
  proposal: string
  status: string
  created_at: string
}

interface AppState {
  agents: Agent[]
  tasks: Task[]
  applications: Application[]
  connected: boolean
  selectedAgent: string | null
  setAgents: (agents: Agent[]) => void
  updateAgentStatus: (name: string, status: Agent['status']) => void
  setTasks: (tasks: Task[]) => void
  setApplications: (apps: Application[]) => void
  setConnected: (connected: boolean) => void
  selectAgent: (name: string | null) => void
}

export const useStore = create<AppState>((set) => ({
  agents: [],
  tasks: [],
  applications: [],
  connected: false,
  selectedAgent: null,
  setAgents: (agents) => set({ agents }),
  updateAgentStatus: (name, status) =>
    set((state) => ({
      agents: state.agents.map((a) =>
        a.name === name ? { ...a, status } : a
      ),
    })),
  setTasks: (tasks) => set({ tasks }),
  setApplications: (applications) => set({ applications }),
  setConnected: (connected) => set({ connected }),
  selectAgent: (selectedAgent) => set({ selectedAgent }),
}))

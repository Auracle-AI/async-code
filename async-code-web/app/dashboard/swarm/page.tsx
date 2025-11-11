"use client"

/**
 * Swarm Visualization Dashboard
 * ==============================
 * Real-time visualization of claude-flow swarm agent activity.
 *
 * Author: Claude Code
 * Date: 2025-11-11
 */

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

interface Agent {
  id: string
  type: string
  status: 'active' | 'idle' | 'completed'
  task: string | null
  performance: number
}

interface SwarmMetrics {
  activeAgents: number
  totalTasks: number
  avgExecutionTime: number
  successRate: number
}

export default function SwarmDashboard() {
  const [agents, setAgents] = useState<Agent[]>([])
  const [metrics, setMetrics] = useState<SwarmMetrics>({
    activeAgents: 0,
    totalTasks: 0,
    avgExecutionTime: 0,
    successRate: 0
  })
  const [selectedTask, setSelectedTask] = useState<number | null>(null)

  useEffect(() => {
    // Fetch swarm data
    fetchSwarmData()

    // Poll for updates every 2 seconds
    const interval = setInterval(fetchSwarmData, 2000)

    return () => clearInterval(interval)
  }, [])

  const fetchSwarmData = async () => {
    try {
      // In production, this would fetch from API
      // const response = await fetch('/api/swarm/status')
      // const data = await response.json()

      // Mock data for demonstration
      const mockAgents: Agent[] = [
        { id: '1', type: 'Backend Specialist', status: 'active', task: 'Implementing API endpoints', performance: 0.92 },
        { id: '2', type: 'Frontend Specialist', status: 'active', task: 'Creating UI components', performance: 0.88 },
        { id: '3', type: 'Testing Specialist', status: 'idle', task: null, performance: 0.95 },
        { id: '4', type: 'Security Analyst', status: 'completed', task: 'Completed security review', performance: 0.90 },
        { id: '5', type: 'Code Reviewer', status: 'active', task: 'Reviewing changes', performance: 0.87 }
      ]

      setAgents(mockAgents)
      setMetrics({
        activeAgents: mockAgents.filter(a => a.status === 'active').length,
        totalTasks: 15,
        avgExecutionTime: 45.2,
        successRate: 0.848
      })
    } catch (error) {
      console.error('Failed to fetch swarm data:', error)
    }
  }

  const getAgentColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-500'
      case 'idle':
        return 'bg-yellow-500'
      case 'completed':
        return 'bg-blue-500'
      default:
        return 'bg-gray-500'
    }
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Swarm Intelligence Dashboard</h1>
        <div className="text-sm text-gray-500">
          Last updated: {new Date().toLocaleTimeString()}
        </div>
      </div>

      {/* Metrics Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-500">
              Active Agents
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{metrics.activeAgents}</div>
            <p className="text-xs text-gray-500 mt-1">
              of {agents.length} total
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-500">
              Total Tasks
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{metrics.totalTasks}</div>
            <p className="text-xs text-gray-500 mt-1">
              across all agents
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-500">
              Avg Execution
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{metrics.avgExecutionTime}s</div>
            <p className="text-xs text-gray-500 mt-1">
              per task
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-500">
              Success Rate
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {(metrics.successRate * 100).toFixed(1)}%
            </div>
            <p className="text-xs text-gray-500 mt-1">
              completion rate
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Agent Grid */}
      <Card>
        <CardHeader>
          <CardTitle>Active Agents</CardTitle>
          <CardDescription>
            Current status of all swarm agents
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {agents.map((agent) => (
              <div
                key={agent.id}
                className="border rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
                onClick={() => setSelectedTask(Number(agent.id))}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="font-semibold">{agent.type}</div>
                  <div className={`w-3 h-3 rounded-full ${getAgentColor(agent.status)}`} />
                </div>

                <div className="text-sm text-gray-600 mb-2">
                  {agent.task || 'Idle - awaiting task'}
                </div>

                <div className="flex items-center justify-between text-xs">
                  <span className="text-gray-500">Performance</span>
                  <span className="font-medium">
                    {(agent.performance * 100).toFixed(0)}%
                  </span>
                </div>

                <div className="mt-2 h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-blue-500 transition-all duration-300"
                    style={{ width: `${agent.performance * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Topology Visualization */}
      <Card>
        <CardHeader>
          <CardTitle>Swarm Topology</CardTitle>
          <CardDescription>
            Agent coordination structure (Mesh)
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-64 flex items-center justify-center bg-gray-50 rounded-lg">
            <div className="text-center text-gray-400">
              <svg className="w-16 h-16 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              <p>Interactive topology visualization</p>
              <p className="text-sm">(React Flow integration would go here)</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

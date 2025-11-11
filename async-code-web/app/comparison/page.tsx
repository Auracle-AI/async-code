"use client"

/**
 * Model Comparison Dashboard
 * ===========================
 * Side-by-side comparison of different AI models on same tasks.
 *
 * Author: Claude Code
 * Date: 2025-11-11
 */

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'

interface ModelMetrics {
  model: string
  totalTasks: number
  successRate: number
  avgExecutionTime: number
  avgCost: number
  avgFilesChanged: number
}

interface ComparisonResult {
  prompt: string
  results: {
    [key: string]: {
      status: string
      executionTime: number
      filesChanged: number
      linesChanged: number
      cost: number
      output?: string
    }
  }
}

export default function ModelComparisonDashboard() {
  const [metrics, setMetrics] = useState<ModelMetrics[]>([])
  const [comparisonResults, setComparisonResults] = useState<ComparisonResult[]>([])
  const [selectedModels, setSelectedModels] = useState<string[]>(['claude', 'claude-flow'])

  useEffect(() => {
    fetchMetrics()
    fetchComparisonResults()
  }, [selectedModels])

  const fetchMetrics = async () => {
    // Mock data for demonstration
    const mockMetrics: ModelMetrics[] = [
      {
        model: 'claude',
        totalTasks: 156,
        successRate: 0.75,
        avgExecutionTime: 52.3,
        avgCost: 0.05,
        avgFilesChanged: 2.8
      },
      {
        model: 'codex',
        totalTasks: 89,
        successRate: 0.70,
        avgExecutionTime: 48.1,
        avgCost: 0.04,
        avgFilesChanged: 2.2
      },
      {
        model: 'claude-flow',
        totalTasks: 43,
        successRate: 0.848,
        avgExecutionTime: 31.5,
        avgCost: 0.25,
        avgFilesChanged: 5.4
      }
    ]

    setMetrics(mockMetrics.filter(m => selectedModels.includes(m.model)))
  }

  const fetchComparisonResults = async () => {
    // Mock comparison data
    const mockResults: ComparisonResult[] = [
      {
        prompt: 'Add user authentication with JWT',
        results: {
          claude: {
            status: 'completed',
            executionTime: 48.2,
            filesChanged: 4,
            linesChanged: 287,
            cost: 0.05
          },
          'claude-flow': {
            status: 'completed',
            executionTime: 32.1,
            filesChanged: 6,
            linesChanged: 312,
            cost: 0.24
          }
        }
      },
      {
        prompt: 'Fix bug in login validation',
        results: {
          claude: {
            status: 'completed',
            executionTime: 25.4,
            filesChanged: 1,
            linesChanged: 23,
            cost: 0.03
          },
          codex: {
            status: 'completed',
            executionTime: 22.8,
            filesChanged: 1,
            linesChanged: 18,
            cost: 0.02
          }
        }
      }
    ]

    setComparisonResults(mockResults)
  }

  const getBetterValue = (metric: string, value1: number, value2: number) => {
    const lowerIsBetter = ['avgExecutionTime', 'avgCost']
    if (lowerIsBetter.includes(metric)) {
      return value1 < value2
    }
    return value1 > value2
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Model Comparison</h1>
        <div className="flex gap-2">
          {['claude', 'codex', 'claude-flow'].map(model => (
            <Button
              key={model}
              variant={selectedModels.includes(model) ? 'default' : 'outline'}
              onClick={() => {
                if (selectedModels.includes(model)) {
                  setSelectedModels(selectedModels.filter(m => m !== model))
                } else {
                  setSelectedModels([...selectedModels, model])
                }
              }}
            >
              {model}
            </Button>
          ))}
        </div>
      </div>

      {/* Metrics Comparison */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {metrics.map((metric) => (
          <Card key={metric.model}>
            <CardHeader>
              <CardTitle className="text-lg capitalize">{metric.model}</CardTitle>
              <CardDescription>{metric.totalTasks} tasks completed</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm text-gray-500">Success Rate</span>
                <span className="font-medium">{(metric.successRate * 100).toFixed(1)}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-500">Avg Time</span>
                <span className="font-medium">{metric.avgExecutionTime.toFixed(1)}s</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-500">Avg Cost</span>
                <span className="font-medium">${metric.avgCost.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-500">Files Changed</span>
                <span className="font-medium">{metric.avgFilesChanged.toFixed(1)}</span>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Side-by-Side Comparisons */}
      <Card>
        <CardHeader>
          <CardTitle>Direct Comparisons</CardTitle>
          <CardDescription>
            Same prompts executed on different models
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {comparisonResults.map((result, idx) => (
            <div key={idx} className="border rounded-lg p-4">
              <div className="font-medium mb-4">{result.prompt}</div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {Object.entries(result.results).map(([model, data]) => (
                  <div key={model} className="border rounded p-3 space-y-2">
                    <div className="font-medium capitalize text-sm">{model}</div>

                    <div className="space-y-1 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-500">Status</span>
                        <span className={
                          data.status === 'completed' ? 'text-green-600' : 'text-red-600'
                        }>
                          {data.status}
                        </span>
                      </div>

                      <div className="flex justify-between">
                        <span className="text-gray-500">Time</span>
                        <span>{data.executionTime.toFixed(1)}s</span>
                      </div>

                      <div className="flex justify-between">
                        <span className="text-gray-500">Files</span>
                        <span>{data.filesChanged}</span>
                      </div>

                      <div className="flex justify-between">
                        <span className="text-gray-500">Lines</span>
                        <span>{data.linesChanged}</span>
                      </div>

                      <div className="flex justify-between">
                        <span className="text-gray-500">Cost</span>
                        <span>${data.cost.toFixed(2)}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Performance Charts */}
      <Card>
        <CardHeader>
          <CardTitle>Performance Trends</CardTitle>
          <CardDescription>30-day performance comparison</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-64 flex items-center justify-center bg-gray-50 rounded">
            <div className="text-center text-gray-400">
              <svg className="w-16 h-16 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              <p>Chart visualization</p>
              <p className="text-sm">(Chart.js or Recharts integration)</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

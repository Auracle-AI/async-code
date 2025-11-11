"""
Agent Performance Metrics Tracking
===================================
Track and analyze performance of different AI agents.

Author: Claude Code
Date: 2025-11-11
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from utils.logger import app_logger
import statistics


@dataclass
class AgentPerformanceMetrics:
    """Performance metrics for an agent."""
    agent_type: str
    total_tasks: int
    successful_tasks: int
    failed_tasks: int
    avg_execution_time: float
    avg_agents_used: float  # For claude-flow
    total_cost: float
    success_rate: float
    avg_lines_changed: float
    avg_files_changed: float


class AgentMetricsTracker:
    """
    Track and analyze agent performance metrics.
    """

    def __init__(self):
        self.metrics_cache = {}

    def record_task_completion(
        self,
        task_id: int,
        agent_type: str,
        success: bool,
        execution_time: float,
        agents_used: int = 1,
        cost: float = 0.0,
        files_changed: int = 0,
        lines_changed: int = 0,
        metadata: Dict[str, Any] = None
    ):
        """
        Record metrics for completed task.

        Args:
            task_id: Task ID
            agent_type: Agent type used
            success: Whether task succeeded
            execution_time: Execution time in seconds
            agents_used: Number of agents (for claude-flow)
            cost: Estimated cost
            files_changed: Number of files modified
            lines_changed: Number of lines modified
            metadata: Additional metadata
        """
        app_logger.info(
            "Recording agent metrics",
            task_id=task_id,
            agent_type=agent_type,
            success=success,
            execution_time=execution_time,
            event="agent_metrics_record"
        )

        # In production, store in database
        # DatabaseOperations.store_agent_metrics(...)

        metric_data = {
            'task_id': task_id,
            'agent_type': agent_type,
            'success': success,
            'execution_time': execution_time,
            'agents_used': agents_used,
            'cost': cost,
            'files_changed': files_changed,
            'lines_changed': lines_changed,
            'timestamp': datetime.utcnow().isoformat(),
            'metadata': metadata or {}
        }

        # Store in cache for quick access
        if agent_type not in self.metrics_cache:
            self.metrics_cache[agent_type] = []

        self.metrics_cache[agent_type].append(metric_data)

    def get_agent_performance(
        self,
        agent_type: str,
        days: int = 30
    ) -> AgentPerformanceMetrics:
        """
        Get performance metrics for specific agent.

        Args:
            agent_type: Agent type ('claude', 'codex', 'claude-flow')
            days: Number of days to analyze

        Returns:
            AgentPerformanceMetrics
        """
        # In production, query from database
        # metrics = DatabaseOperations.get_agent_metrics(agent_type, days)

        # For now, use cache
        metrics = self.metrics_cache.get(agent_type, [])

        if not metrics:
            return AgentPerformanceMetrics(
                agent_type=agent_type,
                total_tasks=0,
                successful_tasks=0,
                failed_tasks=0,
                avg_execution_time=0.0,
                avg_agents_used=0.0,
                total_cost=0.0,
                success_rate=0.0,
                avg_lines_changed=0.0,
                avg_files_changed=0.0
            )

        total_tasks = len(metrics)
        successful_tasks = sum(1 for m in metrics if m['success'])
        failed_tasks = total_tasks - successful_tasks

        avg_execution_time = statistics.mean(m['execution_time'] for m in metrics)
        avg_agents_used = statistics.mean(m['agents_used'] for m in metrics)
        total_cost = sum(m['cost'] for m in metrics)
        success_rate = successful_tasks / total_tasks if total_tasks > 0 else 0.0

        avg_files_changed = statistics.mean(m['files_changed'] for m in metrics if m['files_changed'] > 0) if any(m['files_changed'] > 0 for m in metrics) else 0.0
        avg_lines_changed = statistics.mean(m['lines_changed'] for m in metrics if m['lines_changed'] > 0) if any(m['lines_changed'] > 0 for m in metrics) else 0.0

        return AgentPerformanceMetrics(
            agent_type=agent_type,
            total_tasks=total_tasks,
            successful_tasks=successful_tasks,
            failed_tasks=failed_tasks,
            avg_execution_time=avg_execution_time,
            avg_agents_used=avg_agents_used,
            total_cost=total_cost,
            success_rate=success_rate,
            avg_lines_changed=avg_lines_changed,
            avg_files_changed=avg_files_changed
        )

    def compare_agents(self, days: int = 30) -> Dict[str, AgentPerformanceMetrics]:
        """
        Compare performance across all agents.

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary mapping agent type to performance metrics
        """
        agent_types = ['claude', 'codex', 'claude-flow']

        comparison = {}
        for agent_type in agent_types:
            comparison[agent_type] = self.get_agent_performance(agent_type, days)

        return comparison

    def get_leaderboard(self, metric: str = 'success_rate', limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get agent leaderboard sorted by specific metric.

        Args:
            metric: Metric to sort by ('success_rate', 'avg_execution_time', etc.)
            limit: Number of top agents to return

        Returns:
            List of agents with their metrics
        """
        comparison = self.compare_agents()

        # Sort by metric
        sorted_agents = sorted(
            comparison.items(),
            key=lambda x: getattr(x[1], metric),
            reverse=(metric != 'avg_execution_time')  # Lower is better for time
        )

        leaderboard = []
        for rank, (agent_type, metrics) in enumerate(sorted_agents[:limit], 1):
            leaderboard.append({
                'rank': rank,
                'agent_type': agent_type,
                'metric_value': getattr(metrics, metric),
                'metrics': {
                    'total_tasks': metrics.total_tasks,
                    'success_rate': metrics.success_rate,
                    'avg_execution_time': metrics.avg_execution_time,
                    'total_cost': metrics.total_cost
                }
            })

        return leaderboard


# Global metrics tracker
metrics_tracker = AgentMetricsTracker()


if __name__ == "__main__":
    # Test agent metrics
    print("=" * 60)
    print("Agent Metrics Tracker Test")
    print("=" * 60)

    tracker = AgentMetricsTracker()

    # Record some test metrics
    tracker.record_task_completion(
        task_id=1,
        agent_type='claude',
        success=True,
        execution_time=45.2,
        cost=0.05,
        files_changed=3,
        lines_changed=150
    )

    tracker.record_task_completion(
        task_id=2,
        agent_type='claude-flow',
        success=True,
        execution_time=30.5,
        agents_used=5,
        cost=0.25,
        files_changed=8,
        lines_changed=420
    )

    tracker.record_task_completion(
        task_id=3,
        agent_type='codex',
        success=False,
        execution_time=60.0,
        cost=0.04,
        files_changed=0,
        lines_changed=0
    )

    # Get performance
    print("\n--- Agent Performance ---")
    for agent_type in ['claude', 'codex', 'claude-flow']:
        metrics = tracker.get_agent_performance(agent_type)
        print(f"\n{agent_type.upper()}:")
        print(f"  Total Tasks: {metrics.total_tasks}")
        print(f"  Success Rate: {metrics.success_rate:.1%}")
        print(f"  Avg Execution Time: {metrics.avg_execution_time:.1f}s")
        print(f"  Total Cost: ${metrics.total_cost:.2f}")

    # Leaderboard
    print("\n--- Leaderboard (by success rate) ---")
    leaderboard = tracker.get_leaderboard('success_rate')
    for entry in leaderboard:
        print(f"{entry['rank']}. {entry['agent_type']}: {entry['metric_value']:.1%}")

    print("\n" + "=" * 60)

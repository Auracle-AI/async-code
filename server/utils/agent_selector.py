"""
Smart Agent Selection System
=============================
Automatically select the optimal AI agent/model based on task complexity,
repository context, and historical performance.

Author: Claude Code
Date: 2025-11-11
"""

import re
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import numpy as np
from utils.logger import app_logger


class AgentType(Enum):
    """Available agent types."""
    CLAUDE = "claude"
    CODEX = "codex"
    CLAUDE_FLOW = "claude-flow"


@dataclass
class AgentRecommendation:
    """Agent selection recommendation."""
    agent: AgentType
    confidence: float
    reasoning: List[str]
    estimated_cost: float
    estimated_time: float


class ComplexityAnalyzer:
    """Analyze prompt complexity."""

    # Keywords indicating high complexity
    HIGH_COMPLEXITY_KEYWORDS = [
        'architecture', 'refactor', 'migrate', 'redesign', 'implement system',
        'multi-', 'microservice', 'distributed', 'integration', 'end-to-end',
        'authentication', 'authorization', 'security', 'performance optimization'
    ]

    # Keywords indicating medium complexity
    MEDIUM_COMPLEXITY_KEYWORDS = [
        'add feature', 'implement', 'create api', 'build', 'develop',
        'database', 'api endpoint', 'service', 'component'
    ]

    # Keywords indicating low complexity
    LOW_COMPLEXITY_KEYWORDS = [
        'fix bug', 'update', 'change', 'modify', 'add comment', 'rename',
        'simple function', 'helper', 'utility'
    ]

    @staticmethod
    def analyze_prompt(prompt: str) -> float:
        """
        Analyze prompt complexity.

        Returns:
            float: Complexity score from 0.0 (simple) to 1.0 (complex)
        """
        prompt_lower = prompt.lower()
        score = 0.5  # Start with medium complexity

        # Check for high complexity indicators
        high_matches = sum(1 for kw in ComplexityAnalyzer.HIGH_COMPLEXITY_KEYWORDS
                          if kw in prompt_lower)
        if high_matches > 0:
            score += 0.2 * min(high_matches, 3)

        # Check for medium complexity indicators
        medium_matches = sum(1 for kw in ComplexityAnalyzer.MEDIUM_COMPLEXITY_KEYWORDS
                            if kw in prompt_lower)
        if medium_matches > 0:
            score += 0.1 * min(medium_matches, 2)

        # Check for low complexity indicators
        low_matches = sum(1 for kw in ComplexityAnalyzer.LOW_COMPLEXITY_KEYWORDS
                         if kw in prompt_lower)
        if low_matches > 0:
            score -= 0.15 * min(low_matches, 2)

        # Word count factor (longer prompts tend to be more complex)
        word_count = len(prompt.split())
        if word_count > 100:
            score += 0.1
        elif word_count < 20:
            score -= 0.1

        # Multi-file indicator
        if 'files' in prompt_lower or 'multiple' in prompt_lower:
            score += 0.15

        # Code quality keywords
        quality_keywords = ['test', 'documentation', 'type hints', 'error handling']
        quality_matches = sum(1 for kw in quality_keywords if kw in prompt_lower)
        score += 0.05 * quality_matches

        # Clamp between 0 and 1
        return max(0.0, min(1.0, score))


class RepositoryAnalyzer:
    """Analyze repository context."""

    @staticmethod
    def analyze_repository(repo_url: str) -> Dict[str, Any]:
        """
        Analyze repository to determine language and tech stack.

        Returns:
            Dictionary with repository metadata
        """
        # Extract repo name
        repo_name = repo_url.split('/')[-1].replace('.git', '')

        # Detect language from repo name/URL (simplified)
        # In production, this would make API calls to GitHub
        context = {
            'name': repo_name,
            'primary_language': 'python',  # Default
            'framework': None,
            'size': 'medium',
            'has_tests': False
        }

        # Simple heuristics from repo name
        if 'py' in repo_name.lower() or 'python' in repo_name.lower():
            context['primary_language'] = 'python'
        elif 'js' in repo_name.lower() or 'node' in repo_name.lower():
            context['primary_language'] = 'javascript'
        elif 'react' in repo_name.lower():
            context['primary_language'] = 'javascript'
            context['framework'] = 'react'
        elif 'django' in repo_name.lower() or 'flask' in repo_name.lower():
            context['primary_language'] = 'python'
            context['framework'] = 'web'

        return context


class HistoricalPerformanceAnalyzer:
    """Analyze historical task performance."""

    @staticmethod
    def get_similar_tasks(prompt: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Find similar historical tasks.

        Returns:
            List of similar tasks with their performance metrics
        """
        # In production, this would query the database
        # For now, return empty list
        return []

    @staticmethod
    def calculate_success_rate(agent: AgentType, similar_tasks: List[Dict]) -> float:
        """
        Calculate historical success rate for agent on similar tasks.

        Returns:
            float: Success rate from 0.0 to 1.0
        """
        if not similar_tasks:
            # Default success rates based on agent type
            defaults = {
                AgentType.CLAUDE: 0.75,
                AgentType.CODEX: 0.70,
                AgentType.CLAUDE_FLOW: 0.85
            }
            return defaults.get(agent, 0.70)

        # Calculate from historical data
        agent_tasks = [t for t in similar_tasks if t.get('agent') == agent.value]
        if not agent_tasks:
            return 0.70  # Default

        successful = sum(1 for t in agent_tasks if t.get('status') == 'completed')
        return successful / len(agent_tasks)


class SmartAgentSelector:
    """
    Smart agent selection system.

    Analyzes prompt, repository, and historical performance to recommend
    the optimal AI agent for the task.
    """

    def __init__(self):
        self.complexity_analyzer = ComplexityAnalyzer()
        self.repo_analyzer = RepositoryAnalyzer()
        self.history_analyzer = HistoricalPerformanceAnalyzer()

    def select_agent(
        self,
        prompt: str,
        repo_url: str,
        user_preference: Optional[AgentType] = None,
        cost_sensitive: bool = False
    ) -> AgentRecommendation:
        """
        Select the optimal agent for the task.

        Args:
            prompt: Task description
            repo_url: Repository URL
            user_preference: Optional user preference override
            cost_sensitive: Prioritize cost over quality

        Returns:
            AgentRecommendation with selected agent and reasoning
        """
        app_logger.info(
            "Starting agent selection",
            prompt_length=len(prompt),
            repo_url=repo_url,
            event="agent_selection_start"
        )

        reasoning = []

        # 1. Analyze prompt complexity
        complexity_score = self.complexity_analyzer.analyze_prompt(prompt)
        reasoning.append(f"Complexity score: {complexity_score:.2f}")

        # 2. Analyze repository context
        repo_context = self.repo_analyzer.analyze_repository(repo_url)
        reasoning.append(f"Repository language: {repo_context['primary_language']}")

        # 3. Get historical performance
        similar_tasks = self.history_analyzer.get_similar_tasks(prompt)
        reasoning.append(f"Found {len(similar_tasks)} similar historical tasks")

        # 4. Calculate scores for each agent
        scores = {}

        for agent in AgentType:
            score = 0.0

            # Complexity-based scoring
            if agent == AgentType.CLAUDE_FLOW:
                # Claude-flow excels at complex tasks
                if complexity_score > 0.7:
                    score += 0.4
                    reasoning.append(f"{agent.value}: High complexity detected (+0.4)")
                elif complexity_score < 0.3:
                    score -= 0.2
                    reasoning.append(f"{agent.value}: Low complexity, overhead (-0.2)")
            elif agent == AgentType.CLAUDE:
                # Claude good for medium complexity
                if 0.3 <= complexity_score <= 0.7:
                    score += 0.3
                    reasoning.append(f"{agent.value}: Medium complexity (+0.3)")
            elif agent == AgentType.CODEX:
                # Codex good for low complexity, language-specific tasks
                if complexity_score < 0.4:
                    score += 0.3
                    reasoning.append(f"{agent.value}: Low complexity (+0.3)")
                if repo_context['primary_language'] == 'python':
                    score += 0.2
                    reasoning.append(f"{agent.value}: Python detected (+0.2)")

            # Historical performance
            success_rate = self.history_analyzer.calculate_success_rate(agent, similar_tasks)
            score += success_rate * 0.3
            reasoning.append(f"{agent.value}: Historical success rate: {success_rate:.2%}")

            # Cost factor
            if cost_sensitive:
                cost_penalty = {
                    AgentType.CLAUDE: 0.0,
                    AgentType.CODEX: 0.0,
                    AgentType.CLAUDE_FLOW: -0.3  # Penalize expensive option
                }
                score += cost_penalty[agent]
                if cost_penalty[agent] < 0:
                    reasoning.append(f"{agent.value}: Cost penalty ({cost_penalty[agent]})")

            scores[agent] = score

        # 5. Select best agent
        if user_preference and not cost_sensitive:
            selected_agent = user_preference
            confidence = 0.9
            reasoning.append(f"User preference override: {selected_agent.value}")
        else:
            selected_agent = max(scores, key=scores.get)
            # Normalize confidence to 0-1 range
            max_score = max(scores.values())
            min_score = min(scores.values())
            confidence = (scores[selected_agent] - min_score) / (max_score - min_score + 0.001)
            confidence = max(0.5, min(1.0, confidence))  # Clamp to reasonable range

        # 6. Estimate cost and time
        cost_estimates = {
            AgentType.CLAUDE: 0.05,
            AgentType.CODEX: 0.04,
            AgentType.CLAUDE_FLOW: 0.25  # 5x due to multiple agents
        }

        time_estimates = {
            AgentType.CLAUDE: 60.0,
            AgentType.CODEX: 50.0,
            AgentType.CLAUDE_FLOW: 30.0  # Faster due to parallelization
        }

        # Adjust based on complexity
        time_multiplier = 1.0 + (complexity_score * 2.0)
        estimated_time = time_estimates[selected_agent] * time_multiplier

        app_logger.info(
            "Agent selection completed",
            selected_agent=selected_agent.value,
            confidence=confidence,
            complexity_score=complexity_score,
            event="agent_selection_complete"
        )

        return AgentRecommendation(
            agent=selected_agent,
            confidence=confidence,
            reasoning=reasoning,
            estimated_cost=cost_estimates[selected_agent],
            estimated_time=estimated_time
        )


# Global selector instance
selector = SmartAgentSelector()


def get_recommended_agent(
    prompt: str,
    repo_url: str,
    user_preference: Optional[str] = None,
    cost_sensitive: bool = False
) -> Dict[str, Any]:
    """
    Convenience function to get agent recommendation as dict.

    Args:
        prompt: Task description
        repo_url: Repository URL
        user_preference: Optional user preference ('claude', 'codex', 'claude-flow')
        cost_sensitive: Prioritize cost over quality

    Returns:
        Dictionary with recommendation details
    """
    pref_enum = None
    if user_preference:
        try:
            pref_enum = AgentType(user_preference)
        except ValueError:
            pass

    recommendation = selector.select_agent(
        prompt=prompt,
        repo_url=repo_url,
        user_preference=pref_enum,
        cost_sensitive=cost_sensitive
    )

    return {
        'recommended_agent': recommendation.agent.value,
        'confidence': round(recommendation.confidence, 2),
        'reasoning': recommendation.reasoning,
        'estimated_cost': round(recommendation.estimated_cost, 2),
        'estimated_time_seconds': round(recommendation.estimated_time, 1),
        'alternative_agents': [
            {
                'agent': agent.value,
                'suitable': agent != recommendation.agent
            }
            for agent in AgentType
        ]
    }


if __name__ == "__main__":
    # Test the agent selector
    print("=" * 60)
    print("Smart Agent Selector Test")
    print("=" * 60)

    test_cases = [
        {
            'prompt': 'Fix a small bug in the login function',
            'repo_url': 'https://github.com/test/python-app',
            'expected': 'claude'
        },
        {
            'prompt': 'Implement a complete microservices architecture with authentication, API gateway, and service mesh',
            'repo_url': 'https://github.com/test/enterprise-system',
            'expected': 'claude-flow'
        },
        {
            'prompt': 'Add a simple REST API endpoint for user creation',
            'repo_url': 'https://github.com/test/flask-api',
            'expected': 'claude'
        }
    ]

    for i, test in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i} ---")
        print(f"Prompt: {test['prompt'][:60]}...")
        recommendation = get_recommended_agent(
            test['prompt'],
            test['repo_url']
        )
        print(f"Recommended: {recommendation['recommended_agent']}")
        print(f"Confidence: {recommendation['confidence']}")
        print(f"Expected: {test['expected']}")
        print(f"Match: {'✓' if recommendation['recommended_agent'] == test['expected'] else '✗'}")

    print("\n" + "=" * 60)
    print("✅ Agent selector test complete!")

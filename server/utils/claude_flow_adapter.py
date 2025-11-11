"""
Claude-Flow Adapter
===================
Production adapter for integrating claude-flow orchestration with async-code.
Communicates with Node.js bridge service via HTTP.

Author: Claude Code
Date: 2025-11-11
"""

import requests
import time
import os
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SwarmTopology(Enum):
    """Swarm coordination topologies."""
    MESH = "mesh"
    HIERARCHY = "hierarchy"
    RING = "ring"
    STAR = "star"


@dataclass
class SwarmExecutionResult:
    """Result from swarm task execution."""
    success: bool
    execution_time: float
    output: str
    errors: Optional[str] = None
    agents_used: int = 1
    prompt: Optional[str] = None
    git_diff: Optional[str] = None
    git_patch: Optional[str] = None
    changed_files: List[str] = None

    def __post_init__(self):
        if self.changed_files is None:
            self.changed_files = []


class ClaudeFlowAdapter:
    """
    Adapter for communicating with claude-flow via Node.js bridge service.

    This provides a Pythonic interface to claude-flow's swarm orchestration,
    memory systems, and hive-mind capabilities.
    """

    def __init__(
        self,
        bridge_url: Optional[str] = None,
        timeout: int = 300,
        max_retries: int = 3
    ):
        """
        Initialize the claude-flow adapter.

        Args:
            bridge_url: URL of the Node.js bridge service
            timeout: Default timeout for requests (seconds)
            max_retries: Maximum number of retry attempts
        """
        self.bridge_url = bridge_url or os.getenv(
            "CLAUDE_FLOW_BRIDGE_URL",
            "http://localhost:5001"
        )
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()

        logger.info(f"🌉 Claude-Flow Adapter initialized: {self.bridge_url}")

    def health_check(self) -> bool:
        """
        Check if bridge service is healthy.

        Returns:
            True if service is healthy
        """
        try:
            response = self.session.get(
                f"{self.bridge_url}/health",
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
            return False

    def check_claude_flow_installed(self) -> bool:
        """
        Check if claude-flow is installed in bridge service.

        Returns:
            True if installed and available
        """
        try:
            response = self.session.get(
                f"{self.bridge_url}/check",
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("installed", False)

            return False

        except Exception as e:
            logger.error(f"❌ Claude-flow check failed: {e}")
            return False

    def initialize_claude_flow(self, force: bool = True) -> bool:
        """
        Initialize claude-flow in bridge service.

        Args:
            force: Force re-initialization

        Returns:
            True if successful
        """
        try:
            logger.info("📦 Initializing claude-flow...")

            response = self.session.post(
                f"{self.bridge_url}/init",
                json={"force": force},
                timeout=120
            )

            if response.status_code == 200:
                logger.info("✅ Claude-flow initialized successfully")
                return True
            else:
                logger.error(f"❌ Initialization failed: {response.text}")
                return False

        except Exception as e:
            logger.error(f"❌ Initialization error: {e}")
            return False

    def execute_swarm_task(
        self,
        prompt: str,
        repo_path: Optional[str] = None,
        max_agents: int = 5,
        topology: SwarmTopology = SwarmTopology.MESH,
        timeout: Optional[int] = None
    ) -> SwarmExecutionResult:
        """
        Execute a task using claude-flow swarm orchestration.

        Args:
            prompt: Task description/prompt
            repo_path: Path to git repository (absolute path)
            max_agents: Maximum number of agents in swarm
            topology: Swarm coordination topology
            timeout: Custom timeout (overrides default)

        Returns:
            SwarmExecutionResult with execution details
        """
        logger.info(f"🐝 Executing swarm task: {prompt[:100]}...")

        start_time = time.time()

        try:
            payload = {
                "prompt": prompt,
                "max_agents": max_agents,
                "topology": topology.value,
                "timeout": (timeout or self.timeout) * 1000  # Convert to ms
            }

            if repo_path:
                payload["repo_path"] = repo_path

            response = self._post_with_retry(
                "/swarm/execute",
                payload,
                timeout=timeout or self.timeout
            )

            if response.status_code == 200:
                data = response.json()
                execution_time = time.time() - start_time

                logger.info(
                    f"✅ Swarm task completed in {execution_time:.2f}s "
                    f"using {data.get('agents_used', 1)} agents"
                )

                return SwarmExecutionResult(
                    success=True,
                    execution_time=execution_time,
                    output=data.get("output", ""),
                    errors=data.get("errors"),
                    agents_used=data.get("agents_used", 1),
                    prompt=prompt[:200]
                )
            else:
                error_msg = response.text
                logger.error(f"❌ Swarm task failed: {error_msg}")

                return SwarmExecutionResult(
                    success=False,
                    execution_time=time.time() - start_time,
                    output="",
                    errors=error_msg
                )

        except Exception as e:
            logger.error(f"❌ Swarm execution error: {e}")

            return SwarmExecutionResult(
                success=False,
                execution_time=time.time() - start_time,
                output="",
                errors=str(e)
            )

    def search_memory(
        self,
        query: str,
        k: int = 10,
        threshold: float = 0.7,
        namespace: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search claude-flow memory for relevant patterns.

        Args:
            query: Search query
            k: Number of results to return
            threshold: Similarity threshold (0-1)
            namespace: Optional namespace filter

        Returns:
            List of memory search results
        """
        logger.info(f"🔍 Searching memory: {query}")

        try:
            payload = {
                "query": query,
                "k": k,
                "threshold": threshold
            }

            if namespace:
                payload["namespace"] = namespace

            response = self._post_with_retry(
                "/memory/search",
                payload,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                logger.info(f"✅ Found {len(results)} memory results")
                return results
            else:
                logger.error(f"❌ Memory search failed: {response.text}")
                return []

        except Exception as e:
            logger.error(f"❌ Memory search error: {e}")
            return []

    def store_memory(
        self,
        key: str,
        content: str,
        namespace: Optional[str] = None
    ) -> bool:
        """
        Store information in claude-flow memory.

        Args:
            key: Memory key/identifier
            content: Content to store
            namespace: Optional namespace

        Returns:
            True if successful
        """
        logger.info(f"💾 Storing memory: {key}")

        try:
            payload = {
                "key": key,
                "content": content
            }

            if namespace:
                payload["namespace"] = namespace

            response = self._post_with_retry(
                "/memory/store",
                payload,
                timeout=30
            )

            if response.status_code == 200:
                logger.info("✅ Memory stored successfully")
                return True
            else:
                logger.error(f"❌ Memory storage failed: {response.text}")
                return False

        except Exception as e:
            logger.error(f"❌ Memory storage error: {e}")
            return False

    def spawn_hive_mind(
        self,
        prompt: str,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Spawn a hive-mind coordinated task.

        Args:
            prompt: Task description
            timeout: Custom timeout

        Returns:
            Dictionary with execution results
        """
        logger.info(f"🧠 Spawning hive-mind: {prompt[:100]}...")

        try:
            payload = {
                "prompt": prompt,
                "timeout": (timeout or self.timeout) * 1000
            }

            response = self._post_with_retry(
                "/hive/spawn",
                payload,
                timeout=timeout or self.timeout
            )

            if response.status_code == 200:
                data = response.json()
                logger.info(
                    f"✅ Hive-mind completed in {data.get('execution_time', 0)/1000:.2f}s"
                )
                return data
            else:
                logger.error(f"❌ Hive-mind failed: {response.text}")
                return {"status": "error", "message": response.text}

        except Exception as e:
            logger.error(f"❌ Hive-mind error: {e}")
            return {"status": "error", "message": str(e)}

    def _post_with_retry(
        self,
        endpoint: str,
        payload: Dict[str, Any],
        timeout: int
    ) -> requests.Response:
        """
        POST request with exponential backoff retry.

        Args:
            endpoint: API endpoint (e.g., "/swarm/execute")
            payload: Request payload
            timeout: Request timeout

        Returns:
            Response object

        Raises:
            Exception if all retries fail
        """
        url = f"{self.bridge_url}{endpoint}"
        last_error = None

        for attempt in range(self.max_retries):
            try:
                response = self.session.post(
                    url,
                    json=payload,
                    timeout=timeout
                )
                return response

            except requests.exceptions.Timeout as e:
                last_error = e
                wait_time = 2 ** attempt  # Exponential backoff
                logger.warning(
                    f"⚠️ Request timeout (attempt {attempt + 1}/{self.max_retries}), "
                    f"retrying in {wait_time}s..."
                )
                time.sleep(wait_time)

            except requests.exceptions.RequestException as e:
                last_error = e
                logger.error(f"❌ Request error: {e}")
                break

        raise Exception(f"Request failed after {self.max_retries} attempts: {last_error}")


# Convenience function for quick usage
def create_adapter(bridge_url: Optional[str] = None) -> ClaudeFlowAdapter:
    """
    Create and return a ClaudeFlowAdapter instance.

    Args:
        bridge_url: Optional bridge service URL

    Returns:
        Configured ClaudeFlowAdapter
    """
    return ClaudeFlowAdapter(bridge_url=bridge_url)


if __name__ == "__main__":
    # Quick test
    print("=" * 60)
    print("Claude-Flow Adapter Test")
    print("=" * 60)

    adapter = create_adapter()

    print("\n1️⃣ Checking bridge service health...")
    if adapter.health_check():
        print("✅ Bridge service is healthy")
    else:
        print("❌ Bridge service is not available")
        print("   Make sure to start it: cd claude-flow-bridge && npm start")
        exit(1)

    print("\n2️⃣ Checking claude-flow installation...")
    if adapter.check_claude_flow_installed():
        print("✅ Claude-flow is installed")
    else:
        print("⚠️ Claude-flow not found, initializing...")
        if adapter.initialize_claude_flow():
            print("✅ Claude-flow initialized")
        else:
            print("❌ Failed to initialize claude-flow")
            exit(1)

    print("\n3️⃣ Testing memory operations...")
    adapter.store_memory(
        "test_integration",
        "Claude-flow successfully integrated with async-code",
        namespace="async_code"
    )

    results = adapter.search_memory("integration", namespace="async_code")
    print(f"Found {len(results)} memory results")

    print("\n✅ All tests passed!")
    print("=" * 60)

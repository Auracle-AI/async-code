"""
Claude-Flow Integration POC
===========================
Proof of concept for integrating claude-flow orchestration with async-code.
This uses subprocess to call npx claude-flow commands.

Author: Claude Code
Date: 2025-11-11
"""

import subprocess
import json
import os
import tempfile
import time
from typing import Dict, Any, Optional, List
from pathlib import Path


class ClaudeFlowPOC:
    """
    POC for claude-flow integration using subprocess approach.

    This demonstrates feasibility before building a full Node.js bridge service.
    """

    def __init__(self, working_dir: Optional[str] = None):
        """
        Initialize claude-flow POC.

        Args:
            working_dir: Directory where claude-flow operations will run
        """
        self.working_dir = working_dir or tempfile.mkdtemp(prefix="claude_flow_")
        self.claude_flow_cmd = "npx claude-flow@alpha"

    def check_claude_flow_installed(self) -> bool:
        """Check if claude-flow is available."""
        try:
            result = subprocess.run(
                f"{self.claude_flow_cmd} --help",
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode == 0
        except Exception as e:
            print(f"❌ Claude-flow check failed: {e}")
            return False

    def install_claude_flow(self) -> bool:
        """Install claude-flow if not present."""
        try:
            print("📦 Installing claude-flow...")
            result = subprocess.run(
                f"{self.claude_flow_cmd} init --force",
                shell=True,
                capture_output=True,
                text=True,
                timeout=120,
                cwd=self.working_dir
            )

            if result.returncode == 0:
                print("✅ Claude-flow initialized successfully")
                return True
            else:
                print(f"❌ Installation failed: {result.stderr}")
                return False

        except Exception as e:
            print(f"❌ Installation error: {e}")
            return False

    def execute_swarm_task(
        self,
        prompt: str,
        repo_path: Optional[str] = None,
        max_agents: int = 5,
        topology: str = "mesh"
    ) -> Dict[str, Any]:
        """
        Execute a task using claude-flow swarm orchestration.

        Args:
            prompt: Task description/prompt
            repo_path: Optional path to git repository
            max_agents: Maximum number of agents in swarm
            topology: Swarm topology (mesh, hierarchy, etc.)

        Returns:
            Dictionary with execution results
        """
        print(f"🐝 Executing swarm task: {prompt[:50]}...")

        start_time = time.time()

        try:
            # Build command
            cmd = [
                "npx", "claude-flow@alpha", "swarm", prompt,
                "--claude",
                f"--max-agents={max_agents}",
                f"--topology={topology}"
            ]

            # Change to repo directory if provided
            cwd = repo_path if repo_path and os.path.exists(repo_path) else self.working_dir

            # Execute swarm command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                cwd=cwd,
                env={**os.environ, "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY", "")}
            )

            execution_time = time.time() - start_time

            # Parse output
            success = result.returncode == 0

            return {
                "success": success,
                "execution_time": execution_time,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "prompt": prompt,
                "agents_used": self._extract_agents_count(result.stdout),
                "changes_detected": self._detect_file_changes(cwd)
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Task timeout exceeded (5 minutes)",
                "execution_time": time.time() - start_time
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "execution_time": time.time() - start_time
            }

    def execute_memory_search(
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
            List of memory results
        """
        print(f"🔍 Searching memory: {query}")

        try:
            cmd = [
                "npx", "claude-flow@alpha", "memory", "vector-search", query,
                f"--k={k}",
                f"--threshold={threshold}"
            ]

            if namespace:
                cmd.extend([f"--namespace={namespace}"])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=self.working_dir
            )

            if result.returncode == 0:
                # Parse JSON output if available
                try:
                    return json.loads(result.stdout)
                except json.JSONDecodeError:
                    # Return raw output if not JSON
                    return [{"raw_output": result.stdout}]
            else:
                print(f"⚠️ Memory search failed: {result.stderr}")
                return []

        except Exception as e:
            print(f"❌ Memory search error: {e}")
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
        print(f"💾 Storing memory: {key}")

        try:
            cmd = [
                "npx", "claude-flow@alpha", "memory", "store", key, content
            ]

            if namespace:
                cmd.extend([f"--namespace={namespace}"])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=self.working_dir
            )

            success = result.returncode == 0
            if success:
                print("✅ Memory stored successfully")
            else:
                print(f"❌ Memory storage failed: {result.stderr}")

            return success

        except Exception as e:
            print(f"❌ Memory storage error: {e}")
            return False

    def get_git_changes(self, repo_path: str) -> Dict[str, Any]:
        """
        Get git changes after task execution.

        Args:
            repo_path: Path to git repository

        Returns:
            Dictionary with git diff and patch
        """
        try:
            # Get git diff
            diff_result = subprocess.run(
                ["git", "diff"],
                capture_output=True,
                text=True,
                cwd=repo_path
            )

            # Get git diff --cached for staged changes
            staged_result = subprocess.run(
                ["git", "diff", "--cached"],
                capture_output=True,
                text=True,
                cwd=repo_path
            )

            # Get status
            status_result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                cwd=repo_path
            )

            return {
                "diff": diff_result.stdout,
                "staged_diff": staged_result.stdout,
                "status": status_result.stdout,
                "has_changes": bool(diff_result.stdout or staged_result.stdout)
            }

        except Exception as e:
            print(f"❌ Git changes error: {e}")
            return {"error": str(e), "has_changes": False}

    def _extract_agents_count(self, stdout: str) -> int:
        """Extract number of agents used from output."""
        # Try to parse agent count from output
        # This is a heuristic and may need adjustment
        if "agents" in stdout.lower():
            # Look for patterns like "5 agents" or "using 3 agents"
            import re
            match = re.search(r'(\d+)\s+agents?', stdout.lower())
            if match:
                return int(match.group(1))
        return 1  # Default to 1 if not found

    def _detect_file_changes(self, directory: str) -> List[str]:
        """Detect which files were modified."""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                cwd=directory
            )

            # Parse git status output
            changed_files = []
            for line in result.stdout.split("\n"):
                if line.strip():
                    # Format: "XY filename"
                    parts = line.split(maxsplit=1)
                    if len(parts) == 2:
                        changed_files.append(parts[1])

            return changed_files

        except Exception:
            return []


def run_poc_test():
    """Run a simple POC test."""
    print("=" * 60)
    print("Claude-Flow Integration POC Test")
    print("=" * 60)

    poc = ClaudeFlowPOC()

    # Check if claude-flow is available
    print("\n1️⃣ Checking claude-flow availability...")
    if not poc.check_claude_flow_installed():
        print("Installing claude-flow...")
        if not poc.install_claude_flow():
            print("❌ Failed to install claude-flow. Cannot continue.")
            return

    print("✅ Claude-flow is ready\n")

    # Test memory storage
    print("2️⃣ Testing memory storage...")
    poc.store_memory(
        "test_key",
        "This is a test memory entry for async-code integration",
        namespace="poc_test"
    )

    # Test memory search
    print("\n3️⃣ Testing memory search...")
    results = poc.execute_memory_search(
        "async-code integration",
        k=5,
        namespace="poc_test"
    )
    print(f"Found {len(results)} memory results")

    # Test swarm execution with simple task
    print("\n4️⃣ Testing swarm execution...")
    result = poc.execute_swarm_task(
        prompt="Create a simple Python function that adds two numbers",
        max_agents=2
    )

    print(f"\n{'='*60}")
    print("POC Test Results:")
    print(f"{'='*60}")
    print(f"✅ Success: {result['success']}")
    print(f"⏱️  Execution Time: {result['execution_time']:.2f}s")
    print(f"🤖 Agents Used: {result.get('agents_used', 'unknown')}")
    print(f"📝 Changes Detected: {len(result.get('changes_detected', []))} files")

    if result.get('stdout'):
        print(f"\n📄 Output (first 500 chars):")
        print(result['stdout'][:500])

    if result.get('stderr'):
        print(f"\n⚠️  Errors:")
        print(result['stderr'][:500])

    print(f"\n{'='*60}")
    print("POC Test Complete!")
    print(f"{'='*60}")


if __name__ == "__main__":
    run_poc_test()

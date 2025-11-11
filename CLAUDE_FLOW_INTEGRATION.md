# Claude-Flow Integration Guide

## 📋 Overview

This document describes the integration of [claude-flow](https://github.com/ruvnet/claude-flow) - an enterprise-grade AI orchestration platform - with async-code.

### What is Claude-Flow?

Claude-flow is a sophisticated swarm intelligence orchestration platform that coordinates multiple specialized AI agents to work together on complex development tasks. It provides:

- **Swarm Intelligence**: 64+ specialized agents with queen-worker coordination
- **Advanced Memory**: AgentDB vector search + ReasoningBank pattern matching
- **Performance**: 2.8-4.4x speed improvements, 84.8% SWE-Bench success rate
- **Natural Language Skills**: 25 conversational skills that activate automatically

### Integration Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Next.js Frontend                         │
│                   (Port 3000)                               │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP REST API
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    Flask Backend                            │
│                   (Port 5000)                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Task Routing Logic:                                  │  │
│  │ - model='claude' → Docker (claude-code-automation)   │  │
│  │ - model='codex' → Docker (codex-automation)          │  │
│  │ - model='claude-flow' → Claude-Flow Bridge ─────────┼──┼─┐
│  └──────────────────────────────────────────────────────┘  │ │
└─────────────────────────────────────────────────────────────┘ │
                                                                 │
┌────────────────────────────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────┐
│              Claude-Flow Bridge Service                     │
│                (Node.js, Port 5001)                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ REST API:                                            │  │
│  │ - POST /swarm/execute                                │  │
│  │ - POST /memory/search                                │  │
│  │ - POST /memory/store                                 │  │
│  │ - POST /hive/spawn                                   │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────────┬──────────────────────────────────────┘
                       │ subprocess
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Claude-Flow CLI (npx)                          │
│         Swarm Orchestration + Memory Systems                │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

1. **Node.js 18+** (required for claude-flow)
2. **Anthropic API Key** (for Claude access)
3. **Docker & Docker Compose** (for containerized deployment)

### Installation

#### 1. Set Up Claude-Flow Bridge

```bash
# Navigate to bridge directory
cd claude-flow-bridge

# Install dependencies
npm install

# Configure environment
cp .env.example .env

# Edit .env and add your API key
nano .env
```

**Required environment variables:**
```env
BRIDGE_PORT=5001
ANTHROPIC_API_KEY=your_anthropic_api_key_here
LOG_LEVEL=info
```

#### 2. Start Services with Docker Compose

```bash
# From project root
docker-compose up --build

# Or in detached mode
docker-compose up -d --build
```

This will start:
- Frontend (Next.js) on port 3000
- Backend (Flask) on port 5000
- Claude-Flow Bridge on port 5001

#### 3. Test the Integration

```bash
# Test bridge health
curl http://localhost:5001/health

# Expected response:
# {"status":"healthy","service":"claude-flow-bridge","version":"1.0.0"}
```

---

## 📖 Usage

### Creating Tasks with Claude-Flow

When creating a task via the API or UI, set `model` to `claude-flow`:

```bash
curl -X POST http://localhost:5000/start-task \
  -H "Content-Type: application/json" \
  -H "X-User-ID: your-user-id" \
  -d '{
    "prompt": "Add user authentication with JWT tokens",
    "repo_url": "https://github.com/your-org/your-repo",
    "branch": "main",
    "github_token": "your_github_token",
    "model": "claude-flow",
    "project_id": 1
  }'
```

**Response:**
```json
{
  "status": "success",
  "task_id": 42,
  "message": "Task started successfully using claude-flow",
  "orchestrator": "claude-flow"
}
```

### Frontend Integration

In your Next.js frontend, add "claude-flow" as a model option:

```typescript
// components/task-form.tsx
const MODEL_OPTIONS = [
  { value: 'claude', label: 'Claude Code (Docker)' },
  { value: 'codex', label: 'Codex (Docker)' },
  { value: 'claude-flow', label: 'Claude-Flow (Swarm)' } // NEW!
];
```

---

## 🔄 Comparison: Docker vs Claude-Flow

### Traditional Docker Execution

**How it works:**
1. Flask creates Docker container with claude-code or codex
2. Container clones repository
3. Single agent executes task
4. Results captured from container logs
5. Container cleaned up

**Pros:**
- Simple, well-tested
- Isolated execution environment
- Easy debugging (container logs)

**Cons:**
- Single agent (no swarm intelligence)
- No memory/learning between tasks
- Limited to one approach per task
- Resource-intensive (full container per task)

### Claude-Flow Execution

**How it works:**
1. Flask calls Node.js bridge service
2. Bridge spawns claude-flow swarm
3. Multiple specialized agents coordinate on task
4. Agents leverage shared memory systems
5. Results aggregated and returned

**Pros:**
- **Swarm intelligence**: Multiple agents with specialized skills
- **Shared memory**: Agents learn from previous tasks
- **Better quality**: 84.8% SWE-Bench success rate
- **Faster**: 2.8-4.4x speed improvements
- **Adaptive**: Agents self-organize based on task complexity

**Cons:**
- More complex setup (Node.js bridge required)
- Additional service to maintain
- Higher API costs (multiple agents)
- Newer, less battle-tested

### When to Use Each

| Scenario | Recommended | Reason |
|----------|-------------|---------|
| Simple code changes | Docker (claude/codex) | Faster setup, lower cost |
| Complex features | Claude-Flow | Better coordination, higher quality |
| Learning from history | Claude-Flow | Memory systems retain knowledge |
| Tight deadline | Docker | More predictable timing |
| High quality requirements | Claude-Flow | 84.8% success rate |
| Resource constraints | Docker | Lower API costs |

---

## 🧪 Testing

### Manual Testing

#### 1. Test Bridge Service

```bash
# Health check
curl http://localhost:5001/health

# Check claude-flow installation
curl http://localhost:5001/check
```

#### 2. Test Python Adapter

```bash
cd server
python -m utils.claude_flow_adapter
```

Expected output:
```
============================================================
Claude-Flow Adapter Test
============================================================

1️⃣ Checking bridge service health...
✅ Bridge service is healthy

2️⃣ Checking claude-flow installation...
✅ Claude-flow is installed

3️⃣ Testing memory operations...
💾 Storing memory: test_integration
✅ Memory stored successfully
🔍 Searching memory: integration
Found 1 memory results

✅ All tests passed!
============================================================
```

#### 3. Test POC Script

```bash
cd server
python utils/claude_flow_poc.py
```

### Automated Testing

Create test tasks to validate the integration:

```python
# test_claude_flow_integration.py
import requests

def test_claude_flow_task():
    """Test creating and executing a claude-flow task"""
    response = requests.post(
        "http://localhost:5000/start-task",
        headers={"X-User-ID": "test-user"},
        json={
            "prompt": "Create a simple Python function that adds two numbers",
            "repo_url": "https://github.com/test/repo",
            "branch": "main",
            "github_token": "test_token",
            "model": "claude-flow"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'success'
    assert data['orchestrator'] == 'claude-flow'

    task_id = data['task_id']

    # Poll for completion
    # ... (implement polling logic)

    return task_id
```

---

## 🔧 Configuration

### Environment Variables

#### Backend (Flask)
```env
# server/.env
CLAUDE_FLOW_BRIDGE_URL=http://claude-flow-bridge:5001
ANTHROPIC_API_KEY=your_key_here
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

#### Claude-Flow Bridge
```env
# claude-flow-bridge/.env
BRIDGE_PORT=5001
ANTHROPIC_API_KEY=your_anthropic_key
OPENAI_API_KEY=your_openai_key (optional, for enhanced embeddings)
LOG_LEVEL=info
```

### Docker Compose Configuration

The docker-compose.yml includes the claude-flow-bridge service with:
- Port mapping: 5001:5001
- Volume mounts for persistent memory
- Environment variable injection
- Network connectivity to backend

---

## 📊 Monitoring

### Bridge Service Logs

```bash
# View bridge logs
docker-compose logs -f claude-flow-bridge

# View backend logs
docker-compose logs -f backend
```

### Task Execution Metadata

Tasks executed via claude-flow include additional metadata:

```json
{
  "execution_metadata": {
    "execution_time": 45.2,
    "agents_used": 5,
    "output": "...",
    "orchestrator": "claude-flow",
    "topology": "mesh"
  }
}
```

### Performance Metrics

Monitor these key metrics:
- **Execution time**: Compare with Docker execution
- **Success rate**: Track completed vs failed tasks
- **Agents used**: Average number of agents per task
- **Memory hits**: How often agents leverage previous knowledge

---

## 🐛 Troubleshooting

### Bridge Service Not Starting

**Symptom**: `Connection refused` errors to port 5001

**Solutions**:
1. Check if Node.js 18+ is installed: `node --version`
2. Verify bridge service is running: `docker-compose ps`
3. Check bridge logs: `docker-compose logs claude-flow-bridge`
4. Ensure .env file exists in claude-flow-bridge/

### Claude-Flow Not Installed

**Symptom**: `npx: command not found` or `claude-flow not found`

**Solutions**:
1. Rebuild bridge container: `docker-compose up --build claude-flow-bridge`
2. Manually initialize: `docker-compose exec claude-flow-bridge npx claude-flow@alpha init --force`
3. Check npm is working: `docker-compose exec claude-flow-bridge npm --version`

### Task Execution Fails

**Symptom**: Tasks stuck in "running" or fail immediately

**Solutions**:
1. Check ANTHROPIC_API_KEY is set correctly
2. Verify GitHub token has correct permissions
3. Check repository is accessible
4. Review backend logs for detailed errors: `docker-compose logs backend`

### Memory/Performance Issues

**Symptom**: High memory usage or slow responses

**Solutions**:
1. Limit max_agents in swarm execution (default: 5)
2. Increase timeout values
3. Clear claude-flow cache: `docker volume rm async-code_claude_flow_data`
4. Restart services: `docker-compose restart`

---

## 🔐 Security Considerations

### API Keys
- Store API keys in .env files (never commit to git)
- Use separate keys for development and production
- Rotate keys regularly

### Network Security
- Bridge service only exposed to localhost by default
- Use reverse proxy with authentication for production
- Enable HTTPS for production deployments

### Container Security
- Bridge runs as non-root user
- No privileged access required
- Isolated from host filesystem (except mounted volumes)

---

## 🚀 Production Deployment

### Recommended Architecture

```
Internet
   ↓
[Load Balancer / Nginx]
   ↓
[Frontend Container] ←→ [Backend Container] ←→ [Claude-Flow Bridge]
                              ↓
                       [Supabase Database]
```

### Production Checklist

- [ ] Set `LOG_LEVEL=warn` or `error` in production
- [ ] Use production-grade API keys
- [ ] Enable HTTPS/TLS
- [ ] Configure rate limiting
- [ ] Set up monitoring/alerting
- [ ] Configure backups for claude_flow_data volume
- [ ] Use Docker secrets instead of .env files
- [ ] Set resource limits in docker-compose (memory, CPU)

### Scaling

For high-volume deployments:

1. **Horizontal Scaling**: Run multiple bridge instances behind load balancer
2. **Resource Allocation**: Allocate 2GB+ RAM per bridge instance
3. **Queue System**: Replace threading with Redis queue (RQ, Celery)
4. **Memory Sharing**: Use centralized memory store (Redis, dedicated service)

---

## 📚 Additional Resources

- **Claude-Flow GitHub**: https://github.com/ruvnet/claude-flow
- **Claude-Flow Docs**: See README in claude-flow repository
- **Async-Code Docs**: See main README.md
- **Support**: File issues on GitHub repository

---

## 🤝 Contributing

To improve this integration:

1. Test thoroughly with various task types
2. Document issues and edge cases
3. Propose optimizations via pull requests
4. Share performance benchmarks

---

## 📝 Changelog

### Version 1.0.0 (2025-11-11)
- Initial claude-flow integration
- Added Node.js bridge service
- Created Python adapter with HTTP client
- Updated tasks.py with model routing
- Added docker-compose configuration
- Created comprehensive documentation

---

## ❓ FAQ

**Q: Can I use claude-flow and Docker execution simultaneously?**
A: Yes! They run independently. Choose model per task.

**Q: Does claude-flow replace Docker completely?**
A: No, it's an additional option. Docker execution remains available.

**Q: How much does claude-flow cost?**
A: More expensive than single-agent (5 agents = 5x API calls), but higher quality.

**Q: Can I customize the number of agents?**
A: Yes, modify `max_agents` parameter in `claude_flow_executor.py`.

**Q: Does memory persist between restarts?**
A: Yes, if using Docker volume `claude_flow_data`. Destroy volume to reset.

**Q: Can I use claude-flow without Docker?**
A: Yes, run bridge service standalone: `cd claude-flow-bridge && npm start`

---

**Last Updated**: 2025-11-11
**Integration Version**: 1.0.0
**Claude-Flow Version**: 2.7.0 (alpha)

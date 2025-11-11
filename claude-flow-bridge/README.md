# Claude-Flow Bridge Service

A Node.js HTTP bridge that enables Python Flask backend to communicate with claude-flow's Node.js-based AI orchestration platform.

## Architecture

```
Flask Backend (Python)
       ↓ HTTP
Claude-Flow Bridge (Node.js) ← This service
       ↓ subprocess
Claude-Flow CLI (Node.js)
       ↓
Swarm Orchestration
```

## Installation

```bash
cd claude-flow-bridge
npm install
cp .env.example .env
# Edit .env with your API keys
```

## Running

### Development
```bash
npm run dev
```

### Production
```bash
npm start
```

The server will start on `http://localhost:5001` (configurable via `BRIDGE_PORT`).

## API Endpoints

### Health Check
```bash
GET /health
```

### Check Claude-Flow Installation
```bash
GET /check
```

### Initialize Claude-Flow
```bash
POST /init
Content-Type: application/json

{
  "force": true
}
```

### Execute Swarm Task
```bash
POST /swarm/execute
Content-Type: application/json

{
  "prompt": "Create a REST API with authentication",
  "repo_path": "/path/to/repo",
  "max_agents": 5,
  "topology": "mesh",
  "timeout": 300000
}
```

**Response:**
```json
{
  "status": "success",
  "execution_time": 45230,
  "output": "...",
  "errors": "",
  "prompt": "Create a REST API...",
  "agents_used": 5
}
```

### Memory Vector Search
```bash
POST /memory/search
Content-Type: application/json

{
  "query": "authentication flow",
  "k": 10,
  "threshold": 0.7,
  "namespace": "backend"
}
```

### Store Memory
```bash
POST /memory/store
Content-Type: application/json

{
  "key": "api_design",
  "content": "REST API follows OpenAPI 3.0 spec...",
  "namespace": "backend"
}
```

### Hive-Mind Spawn
```bash
POST /hive/spawn
Content-Type: application/json

{
  "prompt": "Build enterprise system with microservices",
  "timeout": 300000
}
```

## Docker Support

### Build
```bash
docker build -t claude-flow-bridge .
```

### Run
```bash
docker run -p 5001:5001 \
  -e ANTHROPIC_API_KEY=your_key \
  claude-flow-bridge
```

## Integration with Flask

See `server/utils/claude_flow_adapter.py` for Python integration examples.

## Configuration

All configuration via environment variables (see `.env.example`).

## Logs

Uses `pino` logger with pretty printing in development. Logs include:
- Request/response information
- Claude-flow command execution
- Errors and warnings
- Performance metrics

## Security

- CORS restricted to `localhost:3000` and `localhost:5000`
- No authentication (runs locally, trusted network)
- For production: Add JWT/API key authentication

## Troubleshooting

### "npx: command not found"
Install Node.js 18+ and npm.

### "ANTHROPIC_API_KEY not set"
Add your key to `.env` file.

### Timeout errors
Increase `timeout` parameter in requests (default: 5 minutes).

## License

MIT

/**
 * Claude-Flow Bridge Server
 * ==========================
 * Express server that provides HTTP API for Python Flask backend
 * to interact with claude-flow Node.js orchestration.
 *
 * Author: Claude Code
 * Date: 2025-11-11
 */

import express from 'express';
import cors from 'cors';
import bodyParser from 'body-parser';
import dotenv from 'dotenv';
import pino from 'pino';
import { spawn } from 'child_process';
import { promises as fs } from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Load environment
dotenv.config();

// Initialize logger
const logger = pino({
  transport: {
    target: 'pino-pretty',
    options: {
      colorize: true,
      translateTime: 'SYS:standard',
      ignore: 'pid,hostname'
    }
  }
});

// Initialize Express
const app = express();
const PORT = process.env.BRIDGE_PORT || 5001;

// Middleware
app.use(cors({
  origin: ['http://localhost:5000', 'http://localhost:3000'],
  credentials: true
}));
app.use(bodyParser.json({ limit: '10mb' }));
app.use(bodyParser.urlencoded({ extended: true }));

// Request logging
app.use((req, res, next) => {
  logger.info({ method: req.method, path: req.path }, 'Incoming request');
  next();
});

// ============================================================================
// CLAUDE-FLOW INTEGRATION
// ============================================================================

/**
 * Execute claude-flow command via subprocess
 */
async function executeClaudeFlow(args, options = {}) {
  return new Promise((resolve, reject) => {
    const {
      cwd = process.cwd(),
      timeout = 300000, // 5 minutes
      env = {}
    } = options;

    logger.info({ args, cwd }, 'Executing claude-flow command');

    const childEnv = {
      ...process.env,
      ...env,
      ANTHROPIC_API_KEY: process.env.ANTHROPIC_API_KEY || env.ANTHROPIC_API_KEY
    };

    const child = spawn('npx', ['claude-flow@alpha', ...args], {
      cwd,
      env: childEnv,
      shell: true
    });

    let stdout = '';
    let stderr = '';
    let timedOut = false;

    // Setup timeout
    const timeoutId = setTimeout(() => {
      timedOut = true;
      child.kill('SIGTERM');
      setTimeout(() => child.kill('SIGKILL'), 5000);
    }, timeout);

    child.stdout.on('data', (data) => {
      const chunk = data.toString();
      stdout += chunk;
      logger.debug({ chunk }, 'stdout');
    });

    child.stderr.on('data', (data) => {
      const chunk = data.toString();
      stderr += chunk;
      logger.debug({ chunk }, 'stderr');
    });

    child.on('close', (code) => {
      clearTimeout(timeoutId);

      if (timedOut) {
        reject(new Error(`Command timeout after ${timeout}ms`));
      } else if (code === 0) {
        resolve({ stdout, stderr, exitCode: code });
      } else {
        reject(new Error(`Command failed with exit code ${code}: ${stderr}`));
      }
    });

    child.on('error', (error) => {
      clearTimeout(timeoutId);
      reject(error);
    });
  });
}

// ============================================================================
// API ROUTES
// ============================================================================

/**
 * Health check
 */
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    service: 'claude-flow-bridge',
    version: '1.0.0',
    timestamp: new Date().toISOString()
  });
});

/**
 * Check if claude-flow is installed
 */
app.get('/check', async (req, res) => {
  try {
    const result = await executeClaudeFlow(['--help'], { timeout: 30000 });
    res.json({
      status: 'success',
      installed: true,
      message: 'Claude-flow is available'
    });
  } catch (error) {
    logger.error({ error: error.message }, 'Claude-flow check failed');
    res.status(500).json({
      status: 'error',
      installed: false,
      message: error.message
    });
  }
});

/**
 * Initialize claude-flow
 */
app.post('/init', async (req, res) => {
  try {
    const { force = true } = req.body;
    const args = ['init'];
    if (force) args.push('--force');

    const result = await executeClaudeFlow(args, { timeout: 120000 });

    res.json({
      status: 'success',
      message: 'Claude-flow initialized successfully',
      output: result.stdout
    });
  } catch (error) {
    logger.error({ error: error.message }, 'Initialization failed');
    res.status(500).json({
      status: 'error',
      message: error.message
    });
  }
});

/**
 * Execute swarm task
 * POST /swarm/execute
 */
app.post('/swarm/execute', async (req, res) => {
  try {
    const {
      prompt,
      repo_path,
      max_agents = 5,
      topology = 'mesh',
      timeout = 300000
    } = req.body;

    if (!prompt) {
      return res.status(400).json({
        status: 'error',
        message: 'Prompt is required'
      });
    }

    logger.info({ prompt: prompt.substring(0, 100) }, 'Starting swarm execution');

    const args = [
      'swarm',
      prompt,
      '--claude',
      `--max-agents=${max_agents}`,
      `--topology=${topology}`
    ];

    const startTime = Date.now();
    const result = await executeClaudeFlow(args, {
      cwd: repo_path || process.cwd(),
      timeout
    });
    const executionTime = Date.now() - startTime;

    res.json({
      status: 'success',
      execution_time: executionTime,
      output: result.stdout,
      errors: result.stderr,
      prompt: prompt.substring(0, 200),
      agents_used: extractAgentsCount(result.stdout)
    });
  } catch (error) {
    logger.error({ error: error.message }, 'Swarm execution failed');
    res.status(500).json({
      status: 'error',
      message: error.message
    });
  }
});

/**
 * Memory vector search
 * POST /memory/search
 */
app.post('/memory/search', async (req, res) => {
  try {
    const {
      query,
      k = 10,
      threshold = 0.7,
      namespace
    } = req.body;

    if (!query) {
      return res.status(400).json({
        status: 'error',
        message: 'Query is required'
      });
    }

    const args = [
      'memory',
      'vector-search',
      query,
      `--k=${k}`,
      `--threshold=${threshold}`
    ];

    if (namespace) {
      args.push(`--namespace=${namespace}`);
    }

    const result = await executeClaudeFlow(args, { timeout: 30000 });

    // Try to parse JSON output
    let results;
    try {
      results = JSON.parse(result.stdout);
    } catch {
      results = { raw_output: result.stdout };
    }

    res.json({
      status: 'success',
      results,
      query
    });
  } catch (error) {
    logger.error({ error: error.message }, 'Memory search failed');
    res.status(500).json({
      status: 'error',
      message: error.message
    });
  }
});

/**
 * Store in memory
 * POST /memory/store
 */
app.post('/memory/store', async (req, res) => {
  try {
    const { key, content, namespace } = req.body;

    if (!key || !content) {
      return res.status(400).json({
        status: 'error',
        message: 'Key and content are required'
      });
    }

    const args = ['memory', 'store', key, content];

    if (namespace) {
      args.push(`--namespace=${namespace}`);
    }

    const result = await executeClaudeFlow(args, { timeout: 30000 });

    res.json({
      status: 'success',
      message: 'Memory stored successfully',
      key,
      namespace
    });
  } catch (error) {
    logger.error({ error: error.message }, 'Memory storage failed');
    res.status(500).json({
      status: 'error',
      message: error.message
    });
  }
});

/**
 * Hive-mind spawn
 * POST /hive/spawn
 */
app.post('/hive/spawn', async (req, res) => {
  try {
    const { prompt, timeout = 300000 } = req.body;

    if (!prompt) {
      return res.status(400).json({
        status: 'error',
        message: 'Prompt is required'
      });
    }

    const args = ['hive-mind', 'spawn', prompt, '--claude'];

    const startTime = Date.now();
    const result = await executeClaudeFlow(args, { timeout });
    const executionTime = Date.now() - startTime;

    res.json({
      status: 'success',
      execution_time: executionTime,
      output: result.stdout,
      errors: result.stderr
    });
  } catch (error) {
    logger.error({ error: error.message }, 'Hive spawn failed');
    res.status(500).json({
      status: 'error',
      message: error.message
    });
  }
});

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

function extractAgentsCount(output) {
  const match = output.match(/(\d+)\s+agents?/i);
  return match ? parseInt(match[1]) : 1;
}

// ============================================================================
// ERROR HANDLING
// ============================================================================

app.use((err, req, res, next) => {
  logger.error({ err }, 'Unhandled error');
  res.status(500).json({
    status: 'error',
    message: err.message || 'Internal server error'
  });
});

// ============================================================================
// START SERVER
// ============================================================================

app.listen(PORT, () => {
  logger.info(`🚀 Claude-Flow Bridge Server running on http://localhost:${PORT}`);
  logger.info('📡 Ready to receive requests from Flask backend');
});

export default app;

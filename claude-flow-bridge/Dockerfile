FROM node:20-alpine

# Install dependencies for claude-flow
RUN apk add --no-cache \
    python3 \
    py3-pip \
    git \
    bash

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install npm dependencies
RUN npm install

# Install claude-flow globally
RUN npm install -g @anthropic-ai/claude-code

# Copy application code
COPY . .

# Create directory for claude-flow data
RUN mkdir -p /root/.claude-flow

# Expose port
EXPOSE 5001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD node -e "require('http').get('http://localhost:5001/health', (r) => { process.exit(r.statusCode === 200 ? 0 : 1); }).on('error', () => process.exit(1));"

# Start server
CMD ["npm", "start"]

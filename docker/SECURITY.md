# Docker Security Guidelines

## Environment Variables Management

### Security Issues Fixed

1. **Removed direct .env file copying**: The previous Dockerfile.backend copied `.env.example` directly to `.env`, which could expose sensitive configuration data.

2. **Implemented secure environment variable handling**: 
   - Environment variables are now managed through build arguments and runtime injection
   - No sensitive data is baked into the Docker image
   - Validation script ensures required variables are present

### Required Environment Variables

The following environment variables must be provided at runtime:

```bash
# Required (no defaults)
OPENROUTER_API_KEY=your_actual_api_key
SECRET_KEY=your_secure_secret_key

# Optional (have defaults)
GOOGLE_API_KEY=your_google_api_key  # Optional
APP_URL=http://localhost:8000       # Default: http://localhost:8000
APP_TITLE=trippleCheck              # Default: trippleCheck
PORT=8000                           # Default: 8000
HOST=0.0.0.0                       # Default: 0.0.0.0
```

### Deployment Methods

#### 1. Docker Compose (Development)

```bash
# Set environment variables before running
export OPENROUTER_API_KEY="your_api_key"
export SECRET_KEY="your_secret_key"

# Run with docker-compose
docker-compose up
```

#### 2. Docker Run (Production)

```bash
docker run -d \
  -e OPENROUTER_API_KEY="your_api_key" \
  -e SECRET_KEY="your_secret_key" \
  -e GOOGLE_API_KEY="your_google_key" \
  -p 8000:8000 \
  your-image-name
```

#### 3. Kubernetes/Helm

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: tripplecheck-backend
spec:
  template:
    spec:
      containers:
      - name: backend
        image: your-image-name
        env:
        - name: OPENROUTER_API_KEY
          valueFrom:
            secretKeyRef:
              name: tripplecheck-secrets
              key: openrouter-api-key
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: tripplecheck-secrets
              key: secret-key
```

### Security Best Practices

1. **Never commit .env files**: All .env files are gitignored
2. **Use secrets management**: Store sensitive data in Kubernetes secrets, Docker secrets, or external secret managers
3. **Rotate keys regularly**: Implement key rotation policies
4. **Validate environment variables**: The entrypoint script validates required variables
5. **Use non-root user**: Container runs as `appuser` instead of root
6. **Health checks**: Implemented health checks to monitor container status

### Environment Validation

The Docker container includes an entrypoint script that:

- Validates required environment variables are present
- Checks API key format (basic validation)
- Sets default values for optional variables
- Exits with error if validation fails

### Build Arguments

Non-sensitive configuration can be passed as build arguments:

```dockerfile
ARG APP_URL=http://localhost:8000
ARG APP_TITLE=trippleCheck
ARG PORT=8000
ARG HOST=0.0.0.0
```

### Monitoring and Logging

- Health checks monitor container status
- Environment validation logs are available in container logs
- Failed validation prevents container startup

### Compliance

This implementation follows:
- OWASP Docker Security Guidelines
- CIS Docker Benchmark
- 12-Factor App methodology for configuration 
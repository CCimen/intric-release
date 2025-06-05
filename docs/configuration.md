# Intric Configuration Guide

This guide covers all configuration options for the Intric platform.

## Quick Start

**Minimum Required Configuration:**
1. Copy environment templates: `backend/.env.template` → `backend/.env` and `frontend/apps/web/.env.example` → `frontend/apps/web/.env`
2. Set matching `JWT_SECRET` in both files
3. Add at least one AI provider API key (OpenAI, Anthropic, Azure, etc.)
4. Start services - database credentials have working defaults for development

## Backend Configuration

### Database Configuration (Required)

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `POSTGRES_USER` | PostgreSQL username | - | `postgres` |
| `POSTGRES_PASSWORD` | PostgreSQL password | - | `postgres` |
| `POSTGRES_HOST` | PostgreSQL host | - | `localhost` |
| `POSTGRES_PORT` | PostgreSQL port | - | `5432` |
| `POSTGRES_DB` | PostgreSQL database | - | `postgres` |
| `REDIS_HOST` | Redis host | - | `localhost` |
| `REDIS_PORT` | Redis port | - | `6379` |

### Security Configuration (Required)

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `JWT_SECRET` | Secret for JWT signing (must match frontend) | - | `change_me_in_production` |
| `JWT_AUDIENCE` | JWT audience claim | - | `*` |
| `JWT_ISSUER` | JWT issuer | - | `intric` |
| `JWT_EXPIRY_TIME` | Token expiry in seconds | - | `86400` |
| `JWT_ALGORITHM` | JWT algorithm | - | `HS256` |
| `JWT_TOKEN_PREFIX` | Token prefix in header | - | `Bearer` |
| `URL_SIGNING_KEY` | Key for temporary file URLs | - | `change_me_in_production` |
| `API_PREFIX` | API route prefix | - | `/api/v1` |
| `API_KEY_LENGTH` | Generated API key length | - | `64` |
| `API_KEY_HEADER_NAME` | API key header name | - | `X-API-Key` |

### File Upload Limits (Required)

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `UPLOAD_FILE_TO_SESSION_MAX_SIZE` | Max file size for chat uploads (bytes) | - | `1048576` |
| `UPLOAD_IMAGE_TO_SESSION_MAX_SIZE` | Max image size for chat uploads (bytes) | - | `1048576` |
| `UPLOAD_MAX_FILE_SIZE` | Max file size for knowledge base (bytes) | - | `10485760` |
| `TRANSCRIPTION_MAX_FILE_SIZE` | Max audio file size (bytes) | - | `10485760` |
| `MAX_IN_QUESTION` | Max files per question | - | `1` |

### AI Provider Configuration (At least one required)

| Variable | Description | When to Use |
|----------|-------------|------------|
| `OPENAI_API_KEY` | OpenAI API key | For GPT models |
| `ANTHROPIC_API_KEY` | Anthropic API key | For Claude models |
| `AZURE_API_KEY` | Azure OpenAI API key | For Azure-hosted models |
| `AZURE_ENDPOINT` | Azure OpenAI endpoint | With Azure API key |
| `AZURE_API_VERSION` | Azure API version | With Azure API key |
| `INFINITY_URL` | Infinity embedding endpoint | For E5 embedding models |
| `VLLM_MODEL_URL` | VLLM endpoint URL | For self-hosted models |
| `VLLM_API_KEY` | VLLM API key | If VLLM requires auth |
| `OVHCLOUD_API_KEY` | OVHCloud API key | For OVHCloud models |
| `MISTRAL_API_KEY` | Mistral API key | For Mistral models |
| `TAVILY_API_KEY` | Tavily API key | For web search feature |

### Feature Flags (Required)

| Variable | Description | Default | Options |
|----------|-------------|---------|---------|
| `USING_ACCESS_MANAGEMENT` | Enable role-based access control | - | `True`/`False` |
| `USING_AZURE_MODELS` | Enable Azure OpenAI models | - | `True`/`False` |
| `USING_CRAWL` | Enable web crawling feature | - | `True`/`False` |

### Authentication Integration (Optional)

| Variable | Description | When to Use |
|----------|-------------|------------|
| `MOBILITYGUARD_DISCOVERY_ENDPOINT` | OIDC discovery endpoint | For SSO integration |
| `MOBILITYGUARD_CLIENT_ID` | OIDC client ID | With discovery endpoint |
| `MOBILITYGUARD_CLIENT_SECRET` | OIDC client secret | With discovery endpoint |

### Logging (Optional)

| Variable | Description | Default | Options |
|----------|-------------|---------|---------|
| `LOGLEVEL` | Application log level | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |

## Frontend Configuration

### Core Configuration (Required)

| Variable | Description | Example |
|----------|-------------|---------|
| `INTRIC_BACKEND_URL` | Public backend URL (for browser) | `https://intric.example.com` |
| `INTRIC_BACKEND_SERVER_URL` | Internal backend URL (for SSR) | `http://backend:8000` |
| `JWT_SECRET` | Must match backend JWT_SECRET | `change_me_in_production` |
| `ORIGIN` | Frontend public URL | `https://intric.example.com` |

### Feature Configuration (Optional)

| Variable | Description | Default |
|----------|-------------|---------|
| `SHOW_TEMPLATES` | Show application templates | `false` |
| `MOBILITY_GUARD_AUTH` | OIDC provider URL | - |
| `FEEDBACK_FORM_URL` | Feedback form link | - |
| `NODE_ENV` | Node environment | `production` |
| `LOGLEVEL` | Frontend log level | `INFO` |
| `NODE_TLS_REJECT_UNAUTHORIZED` | For internal SSL issues | `0` |

## Container Deployment Configuration

For production deployment using containers, create these environment files:

### `.env` - Container Images
```bash
FRONTEND_IMAGE=your-registry.com/intric/frontend
FRONTEND_TAG=latest
FRONTEND_PORT=3000

BACKEND_IMAGE=your-registry.com/intric/backend
BACKEND_TAG=latest  
BACKEND_PORT=8000

DB_IMAGE=pgvector/pgvector
DB_TAG=pg16

REDIS_IMAGE=redis
REDIS_TAG=latest
```

### `env_backend` - Backend Container
All backend environment variables from above sections

### `env_db` - Database Container
```bash
POSTGRES_USER=postgres
POSTGRES_PASSWORD=secure_password_here
POSTGRES_HOST=db
POSTGRES_PORT=5432
POSTGRES_DB=postgres
```

### `env_frontend` - Frontend Container
All frontend environment variables from above sections

## Development vs Production

### Development Defaults
- Database: `localhost:5432` with password `postgres`
- Redis: `localhost:6379`
- URLs: `http://localhost:8000` (backend), `http://localhost:3000` (frontend)
- JWT_SECRET: Any value, but must match between services

### Production Requirements
- Change all passwords and secrets
- Use HTTPS URLs for `INTRIC_BACKEND_URL` and `ORIGIN`
- Use internal container names for `INTRIC_BACKEND_SERVER_URL` (e.g., `http://backend:8000`)
- Enable SSL termination via reverse proxy
- Set appropriate file upload limits
- Configure at least one AI provider

## URL Configuration Explained

Understanding the difference between URLs is critical for production:

- **`INTRIC_BACKEND_URL`**: The public HTTPS URL that browsers use to reach the backend API
- **`INTRIC_BACKEND_SERVER_URL`**: The internal HTTP URL that the frontend container uses for server-side rendering

This dual configuration prevents:
- CORS issues from mixed HTTP/HTTPS
- SSL certificate validation errors on internal calls
- DNS resolution problems inside containers
- Unnecessary network hops through load balancers

## Configuration Validation

The backend validates all required configuration on startup. Missing required variables will cause the application to fail with clear error messages.

## Additional Resources

- [Development Guide](development-guide.md) - Local development setup
- [Deployment Guide](deployment-guide.md) - Production deployment with examples
- [Troubleshooting Guide](troubleshooting.md) - Common configuration issues
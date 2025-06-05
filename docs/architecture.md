# Intric Architecture

## TLDR

> **Architecture Summary**
>
> - **Core Components**: Frontend (SvelteKit Node.js server), Backend (FastAPI with Gunicorn/Uvicorn), Worker (ARQ/Python), Database (PostgreSQL with pgvector), Cache/Queue (Redis)
> - **Data Flow**: REST API for client interaction, **WebSockets** for status updates, **SSE** for streaming chat responses, background processing via ARQ task queue.
> - **Design Principles**: Domain-driven design, separation of concerns, and clean architecture.
> - **Integration**: Vector search for knowledge retrieval, streaming for real-time responses.
> - **Scalability**: Independent scaling of frontend, backend, and worker components.
> - **Security**: JWT (Bearer token) & API Key Authentication, bcrypt password hashing, RBAC via space memberships.

This document provides a comprehensive overview of the Intric platform architecture, explaining how different components interact and the design principles behind the system.

## Table of Contents
- [Architecture Overview](#architecture-overview)
- [System Components](#system-components)
- [Data Flow](#data-flow)
- [Key Subsystems](#key-subsystems)
- [Security Architecture](#security-architecture)
- [Scaling Considerations](#scaling-considerations)
- [Design Principles](#design-principles)

## Architecture Overview

Intric employs a microservices architecture that separates concerns into distinct components while maintaining a cohesive system. The platform is designed to be:

- **Modular**: Each component has well-defined responsibilities
- **Scalable**: Components can be scaled independently
- **Resilient**: The system can continue operating despite partial failures
- **Secure**: Multi-layered security approach protects data and communications
- **Extensible**: New capabilities can be added without significant architectural changes

## System Components

The Intric platform consists of these primary components:

```mermaid
graph LR
    classDef component fill:#f5f5f5,stroke:#d3d3d3,stroke-width:1px,color:#333

    Frontend["Frontend<br/>(SvelteKit Node.js)"] <---> Backend["Backend<br/>(FastAPI)"]
    Backend <---> Database["Database<br/>(PostgreSQL + pgvector)"]
    Backend <---> Worker["Worker<br/>Service (ARQ)"]
    Worker <---> Redis["Redis<br/>(Cache/Queue/PubSub)"]

    class Frontend,Backend,Database,Worker,Redis component
```
*(Arrows indicate primary data flow directions. Real-time flows via WS/SSE also exist)*

### Frontend Service

| Aspect | Details |
|--------|---------|
| **Technology** | SvelteKit Node.js server (serves application directly) |
| **Responsibility** | Delivers the user interface and manages client-side state |
| **Key Features** | • Responsive UI components<br>• Client-side routing<br>• State management using Svelte stores<br>• Real-time updates via **WebSockets** (for status) and **Server-Sent Events** (for chat streams)<br>• TypeScript for type safety<br>• @intric/intric-js typed API client |

### Backend API

| Aspect | Details |
|--------|---------|
| **Technology** | FastAPI application |
| **Responsibility** | Processes requests, implements business logic, manages authentication |
| **Key Features** | • RESTful API endpoints<br>• JWT Bearer token & API Key authentication<br>• Request validation with Pydantic<br>• Business logic coordination<br>• Multiple LLM provider integration<br>• **WebSocket** endpoint (`/ws`) for real-time status updates<br>• **SSE** endpoints for streaming chat responses |

### Worker Service

| Aspect | Details |
|--------|---------|
| **Technology** | Python service using ARQ task queue |
| **Responsibility** | Handles long-running background tasks |
| **Key Features** | • Document processing<br>• Website crawling<br>• Vector embedding generation<br>• Asynchronous processing via Redis queue<br>• Publishes status updates to Redis |

#### Worker Implementation

The worker service is built on ARQ, a Redis-based task queue. Task definitions follow this pattern:

```python
# Task definition with ARQ
async def process_document_task(ctx, document_id: str):
    """Process a document and generate embeddings."""
    # Fetch document
    document = await get_document(document_id)

    # Process document
    embeddings = process_document(document)

    # Save embeddings
    await save_embeddings(document_id, embeddings)

    return {"status": "completed", "document_id": document_id}
```

Worker configuration follows the ARQ pattern:

```python
# Example based on Codebase/backend/src/intric/worker/arq.py
class WorkerSettings:
    """ARQ worker settings."""
    redis_settings = RedisSettings(host=REDIS_HOST, port=REDIS_PORT) # Simplified
    functions = [
        process_document_task, # Example task
        crawl_website_task,    # Example task
        # ... other tasks
    ]
    on_startup = startup     # Example startup hook
    on_shutdown = shutdown   # Example shutdown hook
```

### Database

| Aspect | Details |
|--------|---------|
| **Technology** | PostgreSQL with pgvector extension |
| **Responsibility** | Persistent storage for structured data and vector embeddings |
| **Key Features** | • Relational data storage<br>• Vector similarity search<br>• ACID transactions<br>• Data integrity |

### Message Broker / Cache

| Aspect | Details |
|--------|---------|
| **Technology** | Redis |
| **Responsibility** | Task queuing via ARQ, caching, **real-time event publishing for WebSockets** |
| **Key Features** | • Task queue for background jobs (ARQ)<br>• Caching layer<br>• Pub/Sub for WebSocket status updates<br>• Temporary data storage |

## Data Flow

### Authentication Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend as Frontend
    participant Backend as Backend API
    participant DB as Database

    User->>Frontend: Access Intric Platform
    Frontend->>Backend: POST /login (Credentials/Token)
    activate Backend
    Backend->>DB: Validate Credentials / API Key
    activate DB
    DB-->>Backend: Auth Response (User Info or Failure)
    deactivate DB
    alt Credentials Valid
        Backend->>Backend: Generate JWT
        Backend-->>Frontend: Return JWT Token (Success)
    else API Key Valid
        Backend-->>Frontend: Return Auth Status (Success)
    else Invalid
        Backend-->>Frontend: Return Error (e.g., 401)
    end
    deactivate Backend
    Frontend->>Frontend: Store JWT Token / Update Auth State
```

### Chat Interaction Flow (Streaming via SSE)

```mermaid
sequenceDiagram
    participant User
    participant Frontend as Frontend (EventSource client)
    participant Backend as Backend API (SSE Endpoint)
    participant DB as Database
    participant LLM as LLM API

    User->>Frontend: Ask Question
    Frontend->>Backend: POST /api/v1/assistants/{id}/sessions/... (stream=true)
    activate Backend
    Backend->>DB: Get Assistant Config, History
    activate DB
    DB-->>Backend: Config, History
    deactivate DB

    Backend->>DB: Vector Search (pgvector)
    activate DB
    DB-->>Backend: Relevant Docs
    deactivate DB

    Backend->>LLM: Send Prompt + Context + Question
    activate LLM
    Note over LLM, Backend: LLM starts generating response
    LLM->>Backend: Stream Chunk 1
    Backend->>Frontend: Send SSE Chunk 1
    LLM->>Backend: Stream Chunk 2
    Backend->>Frontend: Send SSE Chunk 2
    LLM-->>Backend: Final Chunk / End Stream
    deactivate LLM
    Backend->>DB: Save final response, tokens, references etc.
    activate DB
    DB-->>Backend: Save Confirmation
    deactivate DB
    Backend-->>Frontend: Close SSE Connection
    deactivate Backend
    Frontend-->>User: Display Full Response
```

### Real-time Status Update Flow (via WebSockets)

```mermaid
sequenceDiagram
    participant Worker as Worker (Processing Job)
    participant Redis as Redis Pub/Sub
    participant Backend as Backend API (WebSocket Manager)
    participant Frontend as Frontend (WebSocket Client)
    participant User

    activate Worker
    Worker->>Redis: PUBLISH channel:user_id '{"status": "IN_PROGRESS", ...}'
    deactivate Worker
    Note over Redis, Backend: Backend is subscribed to channel:user_id
    Redis->>Backend: Receive Message
    activate Backend
    Backend->>Backend: Find connected WebSocket(s) for user_id
    Backend->>Frontend: Send WS Message '{"type": "app_run_updates", "data": ...}'
    deactivate Backend
    activate Frontend
    Frontend->>Frontend: Update UI state based on message
    Frontend-->>User: Display Updated Job Status
    deactivate Frontend
```

### Document Processing Flow (via ARQ Worker)

```mermaid
sequenceDiagram
    participant User
    participant Frontend as Frontend
    participant Backend as Backend API
    participant Redis as Redis (ARQ Queue & Pub/Sub)
    participant Worker as Worker (ARQ)
    participant DB as Database

    User->>Frontend: Upload Document
    Frontend->>Backend: POST /api/v1/files/
    activate Backend
    Backend->>Redis: Enqueue 'process_document_task' (ARQ Job Queue)
    Backend-->>Frontend: Acknowledge with Job ID
    deactivate Backend

    Worker->>Redis: Poll for Tasks (ARQ Queue)
    Redis->>Worker: Deliver 'process_document_task'
    activate Worker
    Worker->>Redis: PUBLISH status 'IN_PROGRESS' (Pub/Sub)
    Note over Worker: Get File Data, Parse, Chunk
    Worker->>Worker: Generate Embeddings (calls Embedding Model)
    Worker->>DB: Store Document Chunks & Embeddings (pgvector)
    activate DB
    DB-->>Worker: Save Confirmation
    deactivate DB
    Worker->>Redis: PUBLISH status 'COMPLETE' (Pub/Sub)
    Worker->>Redis: Update ARQ Job Status (ARQ Queue)
    deactivate Worker

    Note over Frontend, User: Frontend receives status via WebSocket and updates UI
```

## Key Subsystems

### Knowledge Base Management

| Purpose | Components |
|---------|------------|
| Manages different sources of knowledge that AI can reference | • Document processor (Worker)<br>• Web crawler (Worker)<br>• Embeddings generator (Worker, possibly external model)<br>• Vector search engine (PostgreSQL with pgvector) |

### Assistant Configuration

| Purpose | Components |
|---------|------------|
| Allows creation and customization of AI assistants | • Prompt templates<br>• Knowledge source management<br>• LLM configuration<br>• Behavior settings |

### Conversation Management

| Purpose | Components |
|---------|------------|
| Handles chat interactions between users and AI assistants | • Session management<br>• Context window management<br>• Response generation<br>• Streaming implementation (**SSE** for chat, **WebSockets** for status) |

### Space Management

| Purpose | Components |
|---------|------------|
| Provides collaborative workspaces for teams | • Access control (RBAC via space memberships)<br>• Resource sharing<br>• Collaboration tools |

## Security Architecture

Intric implements a multi-layered security approach:

### Authentication

- **JWT-based authentication**: For user sessions (sent via Authorization header as Bearer token)
- **API key authentication**: For programmatic access (user and assistant-specific keys)
- **Password Hashing**: Uses bcrypt with separate salt storage for securely storing user passwords
- **Optional OIDC**: Integration with providers like MobilityGuard (full OpenID Connect flow)

### Authorization

- **Role-Based Access Control (RBAC)**: Implemented primarily through space memberships
- **Resource-level permissions**: Access controlled based on ownership and membership
- **Space-based isolation**: Resources are typically scoped within spaces

### Data Protection

- **Encrypted data in transit**: TLS/SSL configured typically at the ingress level
- **Secure handling of sensitive information**: API keys and secrets managed via environment variables

### API Security

- **Input validation**: Using Pydantic models in FastAPI
- **Rate limiting**: Recommended implementation at the API gateway or backend level
- **CORS**: Configured via middleware in FastAPI
- **Security headers**: Configurable via FastAPI middleware or reverse proxy

## Production Deployment Considerations

### Typical Production Architecture

In production environments (e.g., Sundsvall kommun using HAProxy and RHEL8), the architecture typically includes:

| Component | Production Setup |
|-----------|------------------|
| **Load Balancer** | HAProxy for distributing traffic and SSL termination (optional) |
| **Frontend Server** | SvelteKit Node.js server serving the application directly |
| **Application Servers** | Multiple FastAPI instances running via Gunicorn/Uvicorn |
| **Container Runtime** | Docker/Podman on RHEL8 |
| **Orchestration** | Docker Compose or Kubernetes |

### Network Architecture

```mermaid
graph LR
    Internet --> HAProxy[HAProxy<br/>Load Balancer]
    HAProxy --> Frontend1[SvelteKit 1]
    HAProxy --> Frontend2[SvelteKit N]
    HAProxy --> API1[FastAPI 1]
    HAProxy --> API2[FastAPI N]
    API1 --> Redis
    API1 --> PostgreSQL
    Worker1[Worker 1] --> Redis
    Worker2[Worker N] --> Redis
```

## Scaling Considerations

Intric is designed to scale in various ways:

### Horizontal Scaling

| Component | Scaling Approach |
|-----------|------------------|
| **Frontend** | Can be load-balanced across multiple SvelteKit Node.js instances |
| **Backend** | Multiple FastAPI instances can run behind a load balancer |
| **Worker** | Multiple ARQ worker instances can consume tasks from the Redis queue |

### Database Scaling

- **Connection Pooling**: Managed by SQLAlchemy
- **Read Replicas**: PostgreSQL supports read replicas for high-read scenarios
- **Indexing**: Proper indexing, including HNSW/IVFFlat for pgvector, is crucial for performance

### Caching Strategy

- **Response Caching**: Can be implemented at API gateway or backend level
- **Data Caching**: Redis can cache frequently accessed data (e.g., user sessions, configurations)
- **Distributed Caching**: Redis provides distributed caching capabilities

## Design Principles

Intric follows these key design principles:

### Domain-Driven Design

- **Bounded Contexts**: Separation by domain (e.g., assistants, spaces, files)
- **Entities and Value Objects**: Modeling the domain (e.g., Space, User)
- **Repositories**: Abstracting data access (e.g., SpaceRepository)
- **Domain Services**: Encapsulating business logic (e.g., SpaceService)

### Clean Architecture

- **Separation of Concerns**: Layers for API, application logic, domain, infrastructure
- **Dependency Inversion**: High-level modules don't depend on low-level modules; both depend on abstractions
- **Use Cases**: Encapsulated in application services
- **Framework Independence**: Core domain logic independent of FastAPI/SvelteKit

### API-First Design

- **Well-defined Contracts**: OpenAPI schema generated by FastAPI
- **Consistent Patterns**: RESTful principles applied
- **Comprehensive Documentation**: Auto-generated Swagger/ReDoc UI
- **Versioning**: Typically via API path (`/api/v1/`)

### Observability

- **Structured Logging**: Configurable logging format and level
- **Metrics**: Integration with monitoring tools (e.g., Prometheus, Grafana) is recommended
- **Tracing**: Can be added using libraries like OpenTelemetry
- **Error Tracking**: Integration with services like Sentry is recommended

### Extensibility

- **LLM Providers**: Designed to potentially support multiple providers
- **Service Interfaces**: Using dependency injection allows swapping implementations
- **Configuration-driven**: Behavior controlled via environment variables

--- END OF UPDATED FILE architecture.md ---

# OAuth2 / OIDC Implementation with FastAPI

> A comprehensive, decoupled demonstration of OAuth2 and OpenID Connect (OIDC) authentication flows with session tracking, role-based access control, and extensible provider architecture.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)

---

## 📋 Table of Contents

1. [🎯 Overview](#-overview)
2. [🏗️ Architecture & Decoupling](#️-architecture--decoupling)
3. [🔄 Implementation Flow](#-implementation-flow)
4. [🐳 Quick Start](#-quick-start)
5. [📊 System Diagrams](#-system-diagrams)
6. [🔧 Configuration](#-configuration)
7. [🚀 API Endpoints](#-api-endpoints)
8. [🧪 Testing](#-testing)
9. [📚 Documentation](#-documentation)

---

## 🎯 Overview

This project demonstrates the practical differences between **OAuth2** (authorization) and **OpenID Connect (OIDC)** (authentication) protocols using a highly modular, decoupled architecture. It supports multiple identity providers with comprehensive session tracking and role-based access control.

### Key Features

- ✅ **Dual Protocol Support**: OAuth2 and OIDC flows side-by-side
- ✅ **Multiple Providers**: GitHub, Azure AD, Google, Auth0
- ✅ **PKCE Security**: Proof Key for Code Exchange implementation
- ✅ **Session Management**: Database-backed session tracking
- ✅ **Role-Based Access**: Dynamic role assignment
- ✅ **Extensible Architecture**: Easy to add new providers
- ✅ **Docker Ready**: Containerized development and production
- ✅ **Hot Reload**: Development with instant code changes

### Supported Providers Matrix

| Provider | OAuth2 | OIDC | PKCE | Refresh Token | Session Tracking |
|----------|--------|------|------|---------------|------------------|
| **GitHub** | ✅ | ❌ | ✅ | ❌ | ✅ |
| **Azure AD** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Google** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Auth0** | ✅ | ✅ | ✅ | ✅ | ✅ |

---

## 🏗️ Architecture & Decoupling

This application demonstrates **extreme decoupling** through layered architecture and dependency injection patterns.

### Core Principles

1. **Single Responsibility**: Each module has one clear purpose
2. **Dependency Inversion**: High-level modules don't depend on low-level modules
3. **Interface Segregation**: Clients depend only on methods they use
4. **Factory Pattern**: Provider instantiation without tight coupling

### Layered Architecture

```mermaid
graph TB
    subgraph "Presentation Layer"
        A[FastAPI Routers]
        B[API Endpoints]
    end

    subgraph "Application Layer"
        C[Auth Services]
        D[Session Service]
        E[Role Service]
    end

    subgraph "Domain Layer"
        F[BaseAuthProvider]
        G[Factory Pattern]
        H[Token Validators]
    end

    subgraph "Infrastructure Layer"
        I[Database Models]
        J[HTTP Clients]
        K[Cache Layer]
        L[Configuration]
    end

    A --> C
    B --> D
    C --> F
    D --> G
    E --> H
    F --> I
    G --> J
    H --> K
    I --> L

    style A fill:#e1f5fe
    style F fill:#f3e5f5
    style I fill:#e8f5e8
```

### Decoupling Benefits

**🔄 Provider Independence**
```mermaid
graph LR
    subgraph "Router Layer"
        R1[GitHub Router]
        R2[Azure Router]
        R3[Google Router]
    end

    subgraph "Factory Layer"
        F[Provider Factory]
    end

    subgraph "Provider Layer"
        P1[GitHub Service]
        P2[Azure Service]
        P3[Google Service]
    end

    R1 --> F
    R2 --> F
    R3 --> F
    F --> P1
    F --> P2
    F --> P3

    style F fill:#fff3e0,stroke:#ff9800
```

- **Routers** don't import provider services directly
- **Factory** manages provider instantiation
- **Providers** register themselves at startup
- **Zero coupling** between router and provider implementations

**🎯 Interface-Based Design**
```mermaid
classDiagram
    class BaseAuthProvider {
        +provider_name: str
        +get_authorization_url(): str
        +exchange_code_for_token(): dict
        +get_user_info(): dict
        +refresh_token(): dict
        +validate_token(): dict
    }

    class GitHubAuthService {
        +provider_name: str
        +get_authorization_url(): str
        +exchange_code_for_token(): dict
        +get_user_info(): dict
    }

    class AzureAuthService {
        +provider_name: str
        +get_authorization_url(): str
        +exchange_code_for_token(): dict
        +get_user_info(): dict
        +refresh_token(): dict
        +validate_token(): dict
    }

    BaseAuthProvider <|-- GitHubAuthService
    BaseAuthProvider <|-- AzureAuthService

    note for GitHubAuthService "OAuth2 Only\nNo refresh/validate"
    note for AzureAuthService "Full OIDC\nWith refresh/validate"
```

**🔌 Plugin Architecture**
```mermaid
sequenceDiagram
    participant App as Application Startup
    participant Router as Auth Router
    participant Factory as Provider Factory
    participant Registry as Provider Registry
    participant Provider as Auth Provider

    App->>Router: Import router module
    Router->>Factory: Import factory
    Factory->>Registry: Access registry
    Registry-->>Factory: Return registered providers
    Factory->>Provider: Instantiate provider
    Provider-->>Factory: Return provider instance
    Factory-->>Router: Return provider
    Router->>Router: Use provider for auth flow
```

### Dependency Injection Flow

```mermaid
graph TD
    A[FastAPI App] --> B[Router Layer]
    B --> C[Service Layer]
    C --> D[Repository Layer]
    D --> E[Infrastructure Layer]

    B -.->|Depends| F[Settings]
    C -.->|Depends| G[Database Session]
    D -.->|Depends| H[Cache]
    E -.->|Depends| I[HTTP Client]

    style A fill:#e3f2fd
    style B fill:#f3e5f5
    style C fill:#fff3e0
    style D fill:#e8f5e8
    style E fill:#fce4ec
```

---

## 🔄 Implementation Flow

### Complete OAuth2/OIDC Flow

```mermaid
sequenceDiagram
    participant User
    participant Browser
    participant FastAPI
    participant Provider as Identity Provider
    participant DB as Database

    rect rgb(240, 248, 255)
        Note over User,DB: Phase 1: Authorization Request
        User->>Browser: Click "Login with X"
        Browser->>FastAPI: GET /auth/x/login
        FastAPI->>FastAPI: Generate state + PKCE
        FastAPI->>DB: Store PKCE verifier
        FastAPI->>Browser: Redirect to Provider auth URL
        Browser->>Provider: GET /authorize with params
        Provider->>Browser: Show login/consent page
        User->>Provider: Authenticate & consent
        Provider->>Browser: Redirect with auth code
        Browser->>FastAPI: GET /auth/x/callback?code=...
    end

    rect rgb(255, 248, 220)
        Note over User,DB: Phase 2: Token Exchange
        FastAPI->>DB: Retrieve PKCE verifier
        FastAPI->>Provider: POST /token (code + PKCE)
        Provider->>FastAPI: Return tokens (access ± id ± refresh)
        FastAPI->>FastAPI: Validate ID token (OIDC only)
        FastAPI->>Provider: GET /userinfo (OAuth2) or decode JWT
        Provider->>FastAPI: Return user info
    end

    rect rgb(240, 255, 240)
        Note over User,DB: Phase 3: Session Creation
        FastAPI->>FastAPI: Assign user roles
        FastAPI->>DB: Create user session
        FastAPI->>Browser: Set session cookie + redirect
        Browser->>FastAPI: Subsequent requests with cookie
        FastAPI->>DB: Validate session
        FastAPI->>Browser: Serve protected content
    end
```

### Provider-Specific Flows

**OAuth2 Flow (GitHub)**
```mermaid
graph TD
    A[User Login] --> B[Generate PKCE]
    B --> C[Store PKCE in Cache]
    C --> D[Redirect to GitHub /authorize]
    D --> E[User Authenticates]
    E --> F[GitHub redirects with code]
    F --> G[Exchange code + PKCE for access_token]
    G --> H[Call GitHub API for user info]
    H --> I[Create session in DB]
    I --> J[Return to app with session]
```

**OIDC Flow (Azure/Google)**
```mermaid
graph TD
    A[User Login] --> B[Generate PKCE]
    B --> C[Store PKCE in Cache]
    C --> D[Redirect to Provider /authorize]
    D --> E[User Authenticates]
    E --> F[Provider redirects with code]
    F --> G[Exchange code + PKCE for tokens]
    G --> H[Validate ID token with JWKS]
    H --> I[Extract user info from JWT]
    I --> J[Create session in DB]
    J --> K[Return to app with session]
    K --> L[Later: Refresh token when needed]
```

### Session Management Flow

```mermaid
stateDiagram-v2
    [*] --> LoginRequest
    LoginRequest --> GenerateState: Create CSRF protection
    GenerateState --> StorePKCE: Generate & store verifier
    StorePKCE --> RedirectToProvider
    RedirectToProvider --> UserAuthenticates
    UserAuthenticates --> ReceiveCallback: With auth code
    ReceiveCallback --> ValidateState
    ValidateState --> ExchangeTokens: Code + PKCE
    ExchangeTokens --> ValidateTokens: OIDC only
    ValidateTokens --> FetchUserInfo
    FetchUserInfo --> AssignRoles
    AssignRoles --> CreateSession
    CreateSession --> SetCookie
    SetCookie --> [*]

    note right of ValidateTokens
        Verify JWT signature
        Check claims (iss, aud, exp)
    end note

    note right of AssignRoles
        Check user attributes
        Assign role based on rules
    end note
```

---

## 🐳 Quick Start

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+

### Development Setup

```bash
# 1. Clone and enter directory
git clone <repository>
cd oidc-oauth2-implementation

# 2. Copy environment template
cp .env.example .env

# 3. Edit .env with your provider credentials
# (See Configuration section below)

# 4. Start development environment
make dev

# 5. Access the application
# - API Docs: http://localhost:8001/docs
# - Health Check: http://localhost:8001/health
```

### Production Setup

```bash
# Start optimized production build
make prod

# Or with docker-compose
DOCKER_MODE=prod docker-compose up -d
```

### Development Workflow

```bash
# Start with hot reload
make dev

# View logs
make logs-app

# Access container shell
make shell

# Run tests
make test

# Stop everything
make down
```

---

## 📊 System Diagrams

### Component Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        Browser[Web Browser]
        Mobile[Mobile App]
    end

    subgraph "API Gateway"
        FastAPI[FastAPI Application<br/>Port 8001]
    end

    subgraph "Authentication Layer"
        Router[Auth Routers<br/>/auth/*]
        Service[Auth Services<br/>Provider-specific]
        Factory[Provider Factory<br/>Dynamic loading]
    end

    subgraph "Business Logic"
        SessionSvc[Session Service<br/>DB operations]
        RoleSvc[Role Service<br/>RBAC logic]
        Cache[Memory Cache<br/>PKCE storage]
    end

    subgraph "Data Layer"
        Postgres[(PostgreSQL<br/>Sessions & Users)]
        Redis[(Redis Cache<br/>Optional)]
    end

    subgraph "External Services"
        GitHub[GitHub OAuth2]
        Azure[Azure AD OIDC]
        Google[Google OIDC]
        Auth0[Auth0 OIDC]
    end

    Browser --> FastAPI
    Mobile --> FastAPI
    FastAPI --> Router
    Router --> Service
    Service --> Factory
    Factory --> GitHub
    Factory --> Azure
    Factory --> Google
    Factory --> Auth0
    Service --> SessionSvc
    Service --> RoleSvc
    Service --> Cache
    SessionSvc --> Postgres
    RoleSvc --> Postgres
    Cache --> Redis

    style FastAPI fill:#e3f2fd,stroke:#1976d2
    style Factory fill:#fff3e0,stroke:#ff9800
    style Postgres fill:#e8f5e8,stroke:#388e3c
```

### Data Flow Architecture

```mermaid
flowchart TD
    A[HTTP Request] --> B{Middleware}
    B --> C[CORS Headers]
    B --> D[Logging]
    B --> E[Exception Handling]

    C --> F{Routing}
    D --> F
    E --> F

    F --> G{OAuth2/OIDC<br/>Endpoints}
    F --> H{Protected<br/>Endpoints}
    F --> I{Health<br/>Endpoints}

    G --> J[Auth Router]
    J --> K[Provider Factory]
    K --> L[Auth Service]
    L --> M[Token Exchange]
    M --> N[User Info Fetch]
    N --> O[Session Creation]
    O --> P[Database Storage]

    H --> Q[Bearer Token<br/>Validation]
    Q --> R[Session Lookup]
    R --> S[Role Check]
    S --> T[Response]

    I --> U[Health Checks]
    U --> V[Database Ping]
    V --> W[Response]

    style B fill:#f3e5f5
    style F fill:#e1f5fe
    style K fill:#fff3e0
    style P fill:#e8f5e8
```

### Deployment Architecture

```mermaid
graph TB
    subgraph "Development"
        DevDocker[Docker Compose<br/>Local]
        DevDB[(PostgreSQL<br/>Local)]
        DevApp[FastAPI App<br/>Hot Reload]
    end

    subgraph "Production"
        ProdDocker[Docker Compose<br/>Server]
        ProdDB[(PostgreSQL<br/>Managed)]
        ProdApp[FastAPI App<br/>Optimized]
        ProdNginx[NGINX<br/>Reverse Proxy]
        ProdSSL[SSL/TLS<br/>Termination]
    end

    subgraph "Cloud Options"
        AWS[AWS ECS/Fargate]
        GCP[Google Cloud Run]
        Azure[Azure Container Apps]
        Railway[Railway.app]
        Render[Render.com]
    end

    DevDocker --> DevDB
    DevDocker --> DevApp

    ProdDocker --> ProdDB
    ProdDocker --> ProdApp
    ProdApp --> ProdNginx
    ProdNginx --> ProdSSL

    ProdDocker -.-> AWS
    ProdDocker -.-> GCP
    ProdDocker -.-> Azure
    ProdDocker -.-> Railway
    ProdDocker -.-> Render

    style DevDocker fill:#e8f5e8
    style ProdDocker fill:#fff3e0
    style AWS fill:#e3f2fd
```

---

## 🔧 Configuration

### Environment Variables

Create a `.env` file with your provider credentials:

```bash
# Application Settings
APP_ENV=development
DEBUG=true
LOG_LEVEL=DEBUG
SECRET_KEY=your-secret-key-here

# Default Provider
AUTH_PROVIDER=github

# GitHub OAuth2
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret
GITHUB_REDIRECT_URI=http://localhost:8001/auth/github/callback

# Azure AD OIDC
AZURE_CLIENT_ID=your_azure_client_id
AZURE_CLIENT_SECRET=your_azure_client_secret
AZURE_REDIRECT_URI=http://localhost:8001/auth/azure/callback
AZURE_TENANT_ID=your_azure_tenant_id

# Google OIDC
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8001/auth/google/callback

# Auth0 OIDC
AUTH0_CLIENT_ID=your_auth0_client_id
AUTH0_CLIENT_SECRET=your_auth0_client_secret
AUTH0_REDIRECT_URI=http://localhost:8001/auth/auth0/callback
AUTH0_DOMAIN=your_auth0_domain.auth0.com

# Database
BACKEND_DB_URL=postgresql://postgres:postgres@localhost:5432/postgres
```

### Provider Setup Guides

See detailed setup instructions in the documentation folder:
- `documentation/OAUTH2_OIDC_SETUP_GUIDE.md` - Complete setup for all providers

---

## 🚀 API Endpoints

### Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/auth/{provider}/login` | Initiate OAuth2/OIDC login |
| `GET` | `/auth/{provider}/callback` | Handle provider callback |
| `POST` | `/auth/logout` | Logout and end session |

### OAuth2 vs OIDC Comparison

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/oauth2/{provider}/login` | OAuth2 flow (access_token only) |
| `GET` | `/oidc/{provider}/login` | OIDC flow (id_token + access_token) |
| `GET` | `/providers` | List all providers and capabilities |
| `POST` | `/logout` | End session |

### Health & Monitoring

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Application health check |
| `GET` | `/docs` | Interactive API documentation |
| `GET` | `/redoc` | Alternative API documentation |

### Example Usage

```bash
# Start login flow
curl http://localhost:8001/oidc/google/login
# Returns: Redirect URL to Google

# Check providers
curl http://localhost:8001/providers

# Health check
curl http://localhost:8001/health
```

---

## 🧪 Testing

### Run Tests

```bash
# Run all tests
make test

# Or with pytest directly
docker-compose exec app pytest

# With coverage
docker-compose exec app pytest --cov=src --cov-report=html
```

### Test Structure

```
tests/
├── unit/              # Unit tests
├── integration/       # Integration tests
├── fixtures/          # Test data
└── conftest.py        # Test configuration
```

### Manual Testing

1. Start the application: `make dev`
2. Visit `http://localhost:8001/docs`
3. Try OAuth2/OIDC flows for different providers
4. Check session persistence and logout

---

## 📚 Documentation

All detailed documentation is available in the `documentation/` folder:

- `README.md` - Original comprehensive guide
- `OAUTH2_OIDC_SETUP_GUIDE.md` - Provider setup instructions
- `FASTAPI_IMPLEMENTATION.md` - FastAPI architecture details
- `DOCKER.md` - Docker setup and deployment
- `OIDC_OAuth2_Flows.md` - Protocol flow diagrams
- `PKCE_README.md` - PKCE security implementation
- `PROVIDER_IMPLEMENTATIONS.md` - Provider-specific details
- `FACTORY_PATTERN_EXPLANATION.md` - Architecture decoupling

### Key Concepts

- **OAuth2**: Authorization framework for API access
- **OIDC**: Authentication layer built on OAuth2
- **PKCE**: Security enhancement for public clients
- **JWT**: JSON Web Tokens for claims
- **JWKS**: JSON Web Key Sets for signature validation

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

### Adding a New Provider

1. Create service in `src/fastapi/services/auth/`
2. Implement `BaseAuthProvider` interface
3. Register with factory: `register_provider("name", ServiceClass)`
4. Add router in `src/fastapi/routers/auth/`
5. Update environment variables
6. Add to provider matrix

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [SQLAlchemy](https://www.sqlalchemy.org/) - Database toolkit
- [Pydantic](https://pydantic-docs.helpmanual.io/) - Data validation
- OAuth2/OIDC provider documentation

---

*Built with ❤️ for learning and demonstrating modern authentication patterns*</content>
<parameter name="filePath">C:\Users\A200125458\Documents\Projects\oidc_oauth2_implementation\README.md

# Synapse — Self-Healing Knowledge Base (PNG4)
### Complete Level 1, Level 2, and Level 3 Implementation

[![CI/CD Pipeline](https://img.shields.io/badge/CI%2FCD-GitHub_Actions-2088FF?logo=github-actions&logoColor=white)](.github/workflows/ci-cd.yml)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI_0.115-009688?logo=fastapi&logoColor=white)](http://127.0.0.1:8000/docs)
[![Python Tests](https://img.shields.io/badge/Tests-17_Passing-success?logo=pytest&logoColor=white)](backend/test_backend.py)
[![Security](https://img.shields.io/badge/Security-JWT_|_PBKDF2_|_RBAC-critical?logo=auth0&logoColor=white)](backend/security.py)
[![Provenance](https://img.shields.io/badge/Ledger-SHA--256_Hash_Chained-blueviolet)](backend/intelligence.py)

Synapse is an enterprise self-healing knowledge base that continuously audits dynamic documentation, detects factual contradictions and stale knowledge, prompts human approval for edge cases, and maintains an immutable cryptographic audit ledger with zero data poisoning risk.

---

## Architecture Levels Implemented

### Level 1: Architecture, Planning & Specifications
- **Comprehensive SRS & Architecture Blueprint**: [`docs/SRS_AND_ARCHITECTURE.md`](docs/SRS_AND_ARCHITECTURE.md)
  - 10 Functional Requirements & Non-Functional Specifications (Security, Performance, Reliability).
  - Complete Mermaid sequence diagrams and continuous 5-stage ingestion/audit pipeline.
  - Relational schema specification for SQLite / PostgreSQL with foreign key constraints.

### Level 2: Core MVP Service & Local Ingestion Pipeline
- **FastAPI Backend Server**: [`backend/api.py`](backend/api.py)
  - REST endpoints for Documents, Findings, History, Policies, and Audits.
  - Interactive Swagger documentation at `http://127.0.0.1:8000/docs`.
- **Reasoning Engine**: [`backend/engine.py`](backend/engine.py)
  - 5-stage continuous audit pipeline.
  - Adversarial prompt-injection quarantine scanner.
  - Policy-guarded auto-healing engine.
  - Append-only compensating rollback mechanism.
- **SQLite Database with WAL Mode**: [`backend/database.py`](backend/database.py)
  - ACID-compliant storage with Write-Ahead Logging.
  - Automated seeding with benchmark test cases: [`backend/seed_data.py`](backend/seed_data.py).

### Level 3: Intelligence, Security, and Real Cloud Deployment
- **Strict Security & Authentication**: [`backend/security.py`](backend/security.py)
  - Salted PBKDF2-SHA256 password hashing (100,000 iterations).
  - RFC 7519 standard HMAC-SHA256 JWT tokens (`/api/auth/login`, `/api/auth/me`).
  - Role-Based Access Control (RBAC) enforcing `Admin`, `Reviewer`, and `Auditor` permissions.
- **Advanced AI & Semantic Vector Intelligence**: [`backend/intelligence.py`](backend/intelligence.py)
  - TF-IDF + Cosine similarity vector contradiction and duplicate detection (`/api/ai/analyze-claim`).
  - Multi-factor calibrated Bayesian confidence scoring (Authority weight + Evidence citation + Policy status).
  - Advanced prompt-injection and data exfiltration defense.
- **Cryptographic Provenance & Tamper-Evident Ledger**:
  - SHA-256 hash-chained append-only Merkle ledger.
  - Verification API (`/api/ledger/verify`) that catches any database record tampering.
- **Automated CI/CD Pipeline**: [`.github/workflows/ci-cd.yml`](.github/workflows/ci-cd.yml)
  - Multi-stage GitHub Actions pipeline: Linting (Ruff/Black), Pytest (17 scenarios), Security AST Scan (Bandit), and Docker build with container healthcheck smoke tests.
- **Containerization & Cloud Infrastructure**:
  - Multi-stage production container [`Dockerfile`](Dockerfile) with non-root user (`UID 10001`).
  - Orchestration via [`docker-compose.yml`](docker-compose.yml) with persistent data volume and healthchecks.
  - Production environment config template: [`.env.example`](.env.example).
  - Complete Cloud Architecture and Kubernetes Manifests: [`docs/CLOUD_DEPLOYMENT.md`](docs/CLOUD_DEPLOYMENT.md).

---

## Quickstart

### 1. Launch with Docker Compose (Recommended for Production)
```bash
cp .env.example .env
docker compose up -d --build
```
Access the application at `http://localhost:8000`.

### 2. Run Locally with Python

```bash
# Install dependencies
pip install -r requirements.txt

# Start FastAPI Server (serves both API and Frontend at port 8000)
python -m uvicorn backend.api:app --host 127.0.0.1 --port 8000
```
- Web Application: **http://127.0.0.1:8000/**
- Interactive Swagger API Docs: **http://127.0.0.1:8000/docs**

---

## Automated Verification Suite

Run all 17 automated tests covering the reasoning engine, security, RBAC, AI vector reasoning, and cryptographic ledger verification:

```bash
python -m pytest backend/ -v
```

### Pre-seeded Enterprise Demo Users
| Role | Email | Password | Allowed Capabilities |
| :--- | :--- | :--- | :--- |
| **Admin** | `alex.sterling@synapse.internal` | `SynapseAdmin2026!` | Full privileges, Policy changes, Rollbacks |
| **Reviewer** | `jordan.lee@synapse.internal` | `Reviewer2026!` | Review queue approvals, Quarantining |
| **Auditor** | `morgan.vance@synapse.internal` | `Auditor2026!` | Read-only access, Ledger verification |

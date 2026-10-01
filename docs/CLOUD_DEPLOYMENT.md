# Synapse Self-Healing Knowledge Base (Level 3)
## Production Cloud Infrastructure & Deployment Architecture

This document specifies the enterprise deployment blueprint for **Synapse**, transforming the local MVP into a secure, highly available, public-facing cloud service.

---

## 1. System Architecture Overview

```
                                  [ Internet / Clients ]
                                             │
                                   HTTPS (TLS 1.3, Port 443)
                                             ▼
                             [ Cloud Application Load Balancer ]
                             (AWS ALB / GCP Cloud Load Balancing)
                                             │
                     ┌───────────────────────┴───────────────────────┐
                     │                                               │
             [ WAF & DDoS Shield ]                          [ SSL Termination ]
                     │                                               │
                     └───────────────────────┬───────────────────────┘
                                             ▼
                               [ Container Service Cluster ]
                                (AWS ECS Fargate / K8s Pods)
                         ┌───────────────────────────────────────┐
                         │ Synapse Container (Port 8000)         │
                         │ ├─ FastAPI ASGI Service (Uvicorn)     │
                         │ ├─ Static Frontend Webpack Mount (/)  │
                         │ ├─ Vector Intelligence Reasoner       │
                         │ └─ Security & RBAC Engine             │
                         └───────────────────┬───────────────────┘
                                             │
                                     Persistent Volume
                               (EFS / Managed Cloud Volume)
                                             ▼
                               ┌───────────────────────────┐
                               │ SQLite Database with WAL  │
                               │ ├─ append-only ledger     │
                               │ ├─ tamper-evident hashes  │
                               │ └─ automated snapshots    │
                               └───────────────────────────┘
```

---

## 2. Security Hardening Specifications

| Security Dimension | Implementation in Synapse | Standard / Compliance |
| :--- | :--- | :--- |
| **Authentication** | HS256 signed JSON Web Tokens (JWT) with expiration | RFC 7519, OAuth 2.0 Bearer |
| **Password Storage** | PBKDF2 with SHA-256, 100,000 iterations & unique 16-byte random salt | NIST SP 800-63B |
| **Role-Based Access (RBAC)** | Role validation middleware (`Admin`, `Reviewer`, `Auditor`) on protected endpoints | Principle of Least Privilege |
| **Container Security** | Non-root user execution (`UID 10001`), read-only root FS where applicable | CIS Docker Benchmark |
| **Adversarial Defense** | Multi-pattern prompt injection & exfiltration quarantine scanner | OWASP Top 10 for LLM Applications |
| **Data Provenance** | Immutable append-only SHA-256 hash-chained Merkle ledger (`/api/ledger/verify`) | ISO 27001 / SOC 2 Type II auditability |

---

## 3. Production Environment Variables

Configure these secrets via AWS Secrets Manager, GCP Secret Manager, or HashiCorp Vault:

```bash
# Server Settings
SYNAPSE_ENV=production
SYNAPSE_HOST=0.0.0.0
SYNAPSE_PORT=8000
SYNAPSE_DEBUG=false

# Cryptographic Keys
SYNAPSE_JWT_SECRET="<generate-64-character-cryptographic-random-secret>"
SYNAPSE_TOKEN_EXPIRY_SECONDS=86400

# Persistence & Storage
SYNAPSE_DB_PATH="/app/data/synapse.db"

# Network & CORS Restrictions
SYNAPSE_CORS_ORIGINS="https://synapse.yourcompany.com,https://app.synapse.io"

# Auto-Healing Safety Gates
SYNAPSE_DEFAULT_AUTO_HEAL_THRESHOLD=95
SYNAPSE_ALLOW_AUTO_HEAL=true
```

---

## 4. Cloud Deployment Options

### Option A: Docker Compose (Single Host / EC2 / Droplet)

For rapid enterprise pilot deployment on a single cloud VM:

```bash
# 1. Clone repository
git clone https://github.com/your-org/synapse-knowledge-base.git
cd synapse-knowledge-base

# 2. Copy and configure secrets
cp .env.example .env
nano .env

# 3. Launch with container healthchecks
docker compose up -d --build

# 4. Verify deployment health
curl http://localhost:8000/api/health
```

### Option B: AWS ECS Fargate Deployment

1. **Push Container to AWS ECR:**
   ```bash
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <aws_account_id>.dkr.ecr.us-east-1.amazonaws.com
   docker build -t synapse-app:latest .
   docker tag synapse-app:latest <aws_account_id>.dkr.ecr.us-east-1.amazonaws.com/synapse-app:latest
   docker push <aws_account_id>.dkr.ecr.us-east-1.amazonaws.com/synapse-app:latest
   ```

2. **Configure Amazon EFS Persistent Storage:**
   - Create an EFS File System in the same VPC as the ECS cluster.
   - Configure an EFS Access Point at `/synapse-data` with POSIX permissions `10001:10001`.
   - Mount to `/app/data` in the ECS Task Definition.

3. **Deploy Task Definition via CloudFormation / Terraform:**
   - Assign Application Load Balancer target group pointing to port 8000 with healthcheck path `/api/health`.

### Option C: Kubernetes Deployment Manifests

```yaml
# synapse-k8s.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: synapse-deployment
  namespace: knowledge-base
  labels:
    app: synapse
spec:
  replicas: 2
  selector:
    matchLabels:
      app: synapse
  template:
    metadata:
      labels:
        app: synapse
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 10001
        fsGroup: 10001
      containers:
      - name: synapse
        image: your-registry.io/synapse-knowledge-base:2.0.0
        ports:
        - containerPort: 8000
        envFrom:
        - secretRef:
            name: synapse-secrets
        resources:
          requests:
            cpu: 500m
            memory: 512Mi
          limits:
            cpu: 2000m
            memory: 1024Mi
        livenessProbe:
          httpGet:
            path: /api/health
            port: 8000
          initialDelaySeconds: 15
          periodSeconds: 20
        readinessProbe:
          httpGet:
            path: /api/health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
        volumeMounts:
        - name: synapse-storage
          mountPath: /app/data
      volumes:
      - name: synapse-storage
        persistentVolumeClaim:
          claimName: synapse-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: synapse-service
  namespace: knowledge-base
spec:
  type: ClusterIP
  ports:
  - port: 80
    targetPort: 8000
  selector:
    app: synapse
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: synapse-ingress
  namespace: knowledge-base
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - synapse.internal.corp
    secretName: synapse-tls-cert
  rules:
  - host: synapse.internal.corp
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: synapse-service
            port:
              number: 80
```

---

## 5. Ledger Integrity & Rollback Procedures

Synapse uses an append-only SHA-256 hash-chained Merkle ledger to guarantee audit tamper-evidence:

### Cryptographic Audit Verification
To verify that no historical records have been modified:
```bash
curl -H "Authorization: Bearer <ADMIN_OR_AUDITOR_JWT_TOKEN>" \
  https://synapse.internal.corp/api/ledger/verify
```
**Expected Response:**
```json
{
  "valid": true,
  "total_events": 42,
  "tip_hash": "a4f8c2b7e193...",
  "status": "Cryptographically verified. All event signatures match."
}
```

### Emergency Rollback
If an incorrect automated or manual change was applied, an authorized Administrator can roll back via:
```bash
curl -X POST \
  -H "Authorization: Bearer <ADMIN_JWT_TOKEN>" \
  https://synapse.internal.corp/api/history/EVT-1001/rollback
```
This action does not delete data; it records an append-only compensating rollback event signed into the hash chain.

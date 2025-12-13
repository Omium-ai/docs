# OMIUM: High-Level Design (HLD)
## Complete Architecture & Tech Stack for AWS + Digital Ocean Deployment

**Version:** 1.0  
**Date:** November 12, 2025  
**Status:** HLD Complete

---

## TABLE OF CONTENTS

1. System Architecture Overview
2. Tech Stack Decisions (Detailed)
3. Deployment Architecture (AWS + Digital Ocean)
4. Communication Patterns
5. Data Flow Diagrams
6. Service Dependencies
7. Scalability & Performance
8. Disaster Recovery & HA
9. Security Architecture
10. Implementation Priorities

---

## 1. SYSTEM ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          OMIUM COMPLETE SYSTEM                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ LAYER 0: CDN & EDGE (AWS CloudFront)                            │  │
│  │ ├─ Frontend assets cache                                        │  │
│  │ ├─ Global distribution (DDoS protection)                        │  │
│  │ ├─ SSL/TLS termination                                          │  │
│  │ └─ Origin: S3 (frontend builds)                                 │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                           ↓ HTTPS ↓                                     │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ LAYER 1: PRESENTATION LAYER (Frontend - AWS S3 + CloudFront)   │  │
│  ├──────────────────────────────────────────────────────────────────┤  │
│  │ ├─ Developer Dashboard (React + WebSocket)                     │  │
│  │ ├─ Operations Dashboard (React + real-time metrics)            │  │
│  │ └─ Compliance Portal (Next.js + server-side rendering)         │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                      ↓ REST + WebSocket ↓                               │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ LAYER 2: API GATEWAY & AUTH (AWS EC2 + ALB)                    │  │
│  ├──────────────────────────────────────────────────────────────────┤  │
│  │ ├─ API Gateway (Kong on EC2)                                   │  │
│  │ ├─ Authentication Service (OAuth2, SAML/OIDC)                  │  │
│  │ ├─ Authorization Service (RBAC, ABAC)                          │  │
│  │ └─ Rate Limiting (Token bucket, per-user)                      │  │
│  │                                                                   │  │
│  │ AWS Load Balancer (ALB) in front                                │  │
│  │ ├─ SSL certificate (ACM)                                        │  │
│  │ ├─ Path-based routing                                           │  │
│  │ └─ Health checks                                                │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                    ↓ gRPC + Service-to-Service ↓                        │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ LAYER 3: CORE MICROSERVICES (AWS EKS Cluster)                  │  │
│  ├──────────────────────────────────────────────────────────────────┤  │
│  │                                                                   │  │
│  │ ┌─────────────────────────────────────────────────────────────┐ │  │
│  │ │ AWS EKS CLUSTER (Multi-AZ, Auto-scaled)                   │ │  │
│  │ ├─────────────────────────────────────────────────────────────┤ │  │
│  │ │ ┌──────────────────────────────────────────────────────┐   │ │  │
│  │ │ │ Istio Service Mesh (mTLS, traffic management)      │   │ │  │
│  │ │ ├──────────────────────────────────────────────────────┤   │ │  │
│  │ │ │ Checkpoint Manager (Go, 3+ replicas)               │   │ │  │
│  │ │ │ Consensus Coordinator (Rust, 3+ replicas)         │   │ │  │
│  │ │ │ Execution Engine (Python, 5-50 replicas)          │   │ │  │
│  │ │ │ Recovery Orchestrator (Python, 3+ replicas)       │   │ │  │
│  │ │ │ Tracing Service (Go, 2+ replicas)                 │   │ │  │
│  │ │ │ Policy Engine (Go, 2+ replicas)                   │   │ │  │
│  │ │ │ Workflow Manager (Python, 2+ replicas)            │   │ │  │
│  │ │ │ Analytics Engine (Python, 1-3 replicas)           │   │ │  │
│  │ │ └──────────────────────────────────────────────────────┘   │ │  │
│  │ │                                                              │ │  │
│  │ │ Persistent Storage:                                          │ │  │
│  │ │ ├─ EBS volumes for StatefulSets                             │ │  │
│  │ │ ├─ Kubernetes ConfigMaps (app config)                       │ │  │
│  │ │ └─ Kubernetes Secrets (API keys, certs)                     │ │  │
│  │ └─────────────────────────────────────────────────────────────┘ │  │
│  │                                                                   │  │
│  │ Event Streaming (Kafka on separate EC2 instances):              │  │
│  │ ├─ Broker cluster (3+ nodes)                                    │  │
│  │ ├─ Topics: execution_events, failures, metrics                 │  │
│  │ └─ Retention: 7 days                                            │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                    ↓ DIGITAL OCEAN for AI Heavy Compute ↓               │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ LAYER 3B: AI COMPUTE (Digital Ocean Droplets)                  │  │
│  ├──────────────────────────────────────────────────────────────────┤  │
│  │ ├─ Execution Engine (Python + GPU support)                      │  │
│  │ │  └─ 2-4 High-Memory Droplets (32GB+ RAM)                      │  │
│  │ │     └─ For heavy LLM inference                                │  │
│  │ ├─ Recovery Orchestrator compute-heavy tasks                    │  │
│  │ │  └─ 1-2 Droplets                                              │  │
│  │ └─ Connection to AWS: Private VPN + Kafka bridge                │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                      ↓ Query & Write ↓                                  │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ LAYER 4: DATA LAYER                                             │  │
│  ├──────────────────────────────────────────────────────────────────┤  │
│  │                                                                   │  │
│  │ AWS RDS (PostgreSQL) - Primary Store                            │  │
│  │ ├─ Multi-AZ deployment                                           │  │
│  │ ├─ Read replicas (2x)                                            │  │
│  │ ├─ Automated backups (35 days)                                   │  │
│  │ └─ Connection pooling (PgBouncer on EC2)                         │  │
│  │                                                                   │  │
│  │ AWS ElastiCache (Redis) - Cache & Sessions                      │  │
│  │ ├─ Cluster mode enabled                                          │  │
│  │ ├─ Multi-AZ (auto-failover)                                      │  │
│  │ └─ Replication across AZs                                        │  │
│  │                                                                   │  │
│  │ AWS DocumentDB (MongoDB) - Flexible schemas                     │  │
│  │ ├─ 3-node cluster (1 primary, 2 read replicas)                  │  │
│  │ ├─ Continuous backups                                            │  │
│  │ └─ Encryption at rest                                            │  │
│  │                                                                   │  │
│  │ AWS S3 - Object Storage                                         │  │
│  │ ├─ Checkpoint state blobs                                        │  │
│  │ ├─ Execution traces                                              │  │
│  │ ├─ Backup archives                                               │  │
│  │ ├─ Versioning enabled                                            │  │
│  │ └─ Server-side encryption (SSE-S3)                               │  │
│  │                                                                   │  │
│  │ AWS Elasticsearch (Managed) - Log indexing                      │  │
│  │ ├─ 3-node cluster                                                │  │
│  │ ├─ Auto-scaling policies                                         │  │
│  │ └─ Kibana for visualization                                      │  │
│  │                                                                   │  │
│  │ AWS Timestream (TimeSeries Metrics)                             │  │
│  │ ├─ Metrics with 1-second granularity                             │  │
│  │ ├─ Auto-scaling storage                                          │  │
│  │ └─ SQL queries                                                   │  │
│  │                                                                   │  │
│  │ Digital Ocean (Optional Secondary Backup)                        │  │
│  │ ├─ PostgreSQL managed database (for read replica)               │  │
│  │ └─ S3 compatible storage (for backup)                            │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                    ↓ Infrastructure Management ↓                        │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ LAYER 5: INFRASTRUCTURE & OPERATIONS                            │  │
│  ├──────────────────────────────────────────────────────────────────┤  │
│  │                                                                   │  │
│  │ AWS Services:                                                     │  │
│  │ ├─ VPC (Virtual Private Cloud)                                  │  │
│  │ │  ├─ Public subnets (NAT gateway)                               │  │
│  │ │  ├─ Private subnets (EKS worker nodes)                         │  │
│  │ │  ├─ Database subnets (RDS, ElastiCache)                        │  │
│  │ │  └─ Multi-AZ (us-east-1a, us-east-1b, us-east-1c)             │  │
│  │ ├─ IAM (Identity & Access Management)                            │  │
│  │ │  ├─ EKS service role                                           │  │
│  │ │  ├─ Node instance role                                         │  │
│  │ │  ├─ Service account roles (for each microservice)             │  │
│  │ │  └─ Cross-account roles (Digital Ocean access)                 │  │
│  │ ├─ KMS (Key Management Service)                                  │  │
│  │ │  ├─ S3 encryption key                                          │  │
│  │ │  ├─ RDS encryption key                                         │  │
│  │ │  └─ Secrets encryption key                                     │  │
│  │ ├─ Secrets Manager                                               │  │
│  │ │  ├─ Database credentials                                       │  │
│  │ │  ├─ API keys                                                   │  │
│  │ │  └─ SSL certificates                                           │  │
│  │ ├─ CloudWatch (Monitoring)                                       │  │
│  │ │  ├─ Metrics (CPU, memory, network)                             │  │
│  │ │  ├─ Logs (aggregated from all services)                        │  │
│  │ │  ├─ Alarms (auto-trigger on thresholds)                        │  │
│  │ │  └─ Dashboards (auto-generated)                                │  │
│  │ ├─ CloudTrail (Audit logging)                                    │  │
│  │ ├─ SNS (Simple Notification Service)                             │  │
│  │ │  └─ Alerts to Slack, email, PagerDuty                          │  │
│  │                                                                   │  │
│  │ GitHub Actions (CI/CD Pipeline):                                 │  │
│  │ ├─ Push to main → Run tests                                      │  │
│  │ ├─ Tests pass → Build Docker images                              │  │
│  │ ├─ Push to ECR (Elastic Container Registry)                      │  │
│  │ ├─ Deploy to staging EKS cluster                                 │  │
│  │ ├─ Run smoke tests                                               │  │
│  │ ├─ Deploy to production EKS cluster                              │  │
│  │ └─ Send Slack notification                                       │  │
│  │                                                                   │  │
│  │ Terraform (Infrastructure as Code):                              │  │
│  │ ├─ VPC configuration                                             │  │
│  │ ├─ EKS cluster setup                                             │  │
│  │ ├─ RDS provisioning                                              │  │
│  │ ├─ S3 bucket creation                                            │  │
│  │ ├─ IAM roles & policies                                          │  │
│  │ └─ All versioned in Git                                          │  │
│  │                                                                   │  │
│  │ Helm (K8s package management):                                   │  │
│  │ ├─ Deploy all 8 microservices                                    │  │
│  │ ├─ Manage dependencies                                           │  │
│  │ └─ Different values for staging vs prod                          │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. TECH STACK DECISIONS (DETAILED & JUSTIFIED)

### 2.1 FRONTEND LAYER

**Components:**
- Developer Dashboard
- Operations Dashboard
- Compliance Portal

**Tech Stack:**

| Layer | Technology | Justification | Alternatives |
|-------|-----------|---------------|--------------|
| **Framework** | React 18 + TypeScript | Type-safe, largest ecosystem, best tooling | Vue 3, Svelte |
| **State Management** | Redux Toolkit (RTK) | Redux standard for large apps, RTK simplifies boilerplate | Zustand, Recoil |
| **Real-time** | WebSocket (Socket.io) | For live execution feeds, low latency | GraphQL subscriptions |
| **Charting** | Recharts + D3.js | Recharts for standard charts, D3 for custom | Chart.js, Plotly |
| **Build Tool** | Vite | 10x faster than Webpack, excellent DX | Webpack, Parcel |
| **Package Manager** | pnpm | Faster, better disk space usage than npm | npm, yarn |
| **CSS** | Tailwind CSS | Utility-first, production-ready | Bootstrap, Material-UI |
| **Component Library** | shadcn/ui | Headless, unstyled, copy-paste components | Chakra, Ant Design |
| **Deployment** | AWS S3 + CloudFront | Static asset CDN, global distribution | Vercel, Netlify |

**Why This Stack:**
- Type-safe development (catches bugs at compile-time)
- Excellent performance (Vite builds 10x faster)
- Large ecosystem (easy to find libraries)
- Perfect for real-time dashboards (WebSocket + React)
- CloudFront provides DDoS protection + global distribution

**Frontend Code Structure:**
```
frontend/
├── developer-dashboard/
│   ├── src/
│   │   ├── pages/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── store/         # Redux state
│   │   ├── services/      # API calls
│   │   ├── types/         # TypeScript types
│   │   └── App.tsx
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── package.json
├── ops-dashboard/        # Similar structure
├── compliance-portal/    # Next.js for SSR
└── shared/
    ├── components/
    ├── hooks/
    ├── utils/
    └── types/
```

**Build & Deploy:**
```bash
# Development
npm run dev              # Local dev server (Vite)

# Production
npm run build           # Builds to dist/
aws s3 sync dist s3://omium-frontend/
aws cloudfront create-invalidation --distribution-id xxx --paths '/*'
```

---

### 2.2 BACKEND LAYER (API Gateway + Auth)

**Tech Stack:**

| Component | Technology | Why |
|-----------|-----------|-----|
| **API Gateway** | Kong (on EC2) | Battle-tested, 10k+ stars, supports plugins, REST + gRPC |
| **Reverse Proxy** | Nginx | Alternative if Kong too heavy, pure performance |
| **Auth Service** | Custom Python (FastAPI) | OAuth2, SAML, JWT, custom business logic |
| **Container Runtime** | Docker | Standard containerization, excellent tooling |
| **Deployment** | AWS EC2 (t3.xlarge, 2x) | Simple, predictable cost, full control |
| **Load Balancer** | AWS ALB (Application Load Balancer) | Layer 7 routing, SSL termination, health checks |

**Why NOT Kubernetes for Backend?**
- API Gateway doesn't need to scale to 50+ instances
- EC2 simpler operational model (fewer things to debug)
- Easier debugging (SSH into instance, check logs directly)
- Lower cost (1-2 instances vs minimum 3 for K8s control plane)

**Backend Architecture:**
```
Internet
  │
  └─ AWS Route53 (DNS)
       │
       └─ AWS ALB (SSL/TLS termination)
            │
            ├─ EC2 Instance 1 (Kong + Auth)
            │   ├─ Kong (API Gateway) :8000
            │   ├─ Auth Service :3000
            │   ├─ Authorization Service :3001
            │   └─ Docker + Nginx
            │
            └─ EC2 Instance 2 (Kong + Auth) [standby/failover]
                └─ Same setup
                
All requests routed through ALB
Health checks every 30 seconds
Auto-recovery on failure
```

**Kong Configuration:**
```yaml
# kong.conf
database: postgres
proxy_listen: 0.0.0.0:8000
admin_listen: 0.0.0.0:8001

plugins_enabled_header: on
log_level: notice
```

**Kong Routes:**
```
/api/v1/execution/*     → execution-engine:7001
/api/v1/checkpoints/*   → checkpoint-manager:7002
/api/v1/consensus/*     → consensus-coordinator:7003
/api/v1/recovery/*      → recovery-orchestrator:7004
/api/v1/traces/*        → tracing-service:7005
/api/v1/policies/*      → policy-engine:7006
/api/v1/workflows/*     → workflow-manager:7007
/api/v1/analytics/*     → analytics-engine:7008
/auth/*                 → auth-service:3000
/admin/*                → authorization-service:3001
```

**Authentication Flow:**
```
POST /auth/oauth/login
  ↓
Auth Service validates credentials with Auth0/Keycloak
  ↓
Returns JWT token
  ↓
Client includes JWT in Authorization header
  ↓
Kong validates token (plugin)
  ↓
Request passes through to backend service
```

---

### 2.3 CORE SERVICES LAYER (AWS EKS)

**Why EKS over ECS or Self-managed Kubernetes?**

| Feature | EKS | ECS | Self-managed K8s |
|---------|-----|-----|-----------------|
| **Ops Overhead** | Low (AWS manages control plane) | Very Low (AWS managed) | HIGH |
| **Kubernetes API** | Yes | No | Yes |
| **Multi-cloud portability** | Yes | No | Yes |
| **Cost** | Medium | Medium | Low (but high ops) |
| **Learning Curve** | Medium | Low | HIGH |
| **Our Choice** | ✅ YES | ❌ No | ❌ No |

**Why EKS?**
- Kubernetes standard API (portable to GCP/Azure later)
- AWS manages control plane (etcd, API servers)
- Deep AWS integration (IAM, VPC, ELB)
- Excellent for stateless microservices
- Native support for service mesh (Istio)

**Tech Stack for Microservices:**

| Service | Language | Framework | Why |
|---------|----------|-----------|-----|
| **Checkpoint Manager** | Go | gRPC + gorums | Performance critical, Raft coordination |
| **Consensus Coordinator** | Rust | Tokio + tonic | Memory safety, correctness, no GC pauses |
| **Execution Engine** | Python | FastAPI + asyncio | LLM SDK compatibility, rapid iteration |
| **Recovery Orchestrator** | Python | FastAPI | ML/analysis for root cause |
| **Tracing Service** | Go | OpenTelemetry SDK | High throughput trace collection |
| **Policy Engine** | Go | OPA (Rego) | Policy as code, fast evaluation |
| **Workflow Manager** | Python | FastAPI | YAML/JSON processing, flexibility |
| **Analytics Engine** | Python | FastAPI + pandas | Data analysis, SQL queries |

**Why Mixed Tech Stack?**
- Use the RIGHT tool for each job
- Go: Performance-critical, distributed systems
- Rust: Memory safety, concurrent data access
- Python: Rapid iteration, extensive LLM libraries

**EKS Cluster Configuration:**

```yaml
# eks-cluster.tf
resource "aws_eks_cluster" "omium" {
  name            = "omium-prod"
  role_arn        = aws_iam_role.eks_cluster_role.arn
  version         = "1.28"  # Latest stable
  
  vpc_config {
    subnet_ids              = var.subnet_ids
    security_group_ids      = [aws_security_group.eks.id]
    endpoint_private_access = true
    endpoint_public_access  = false  # Private only
  }
  
  enabled_cluster_log_types = ["api", "audit", "authenticator", "controllerManager", "scheduler"]
  
  # Enable Container Insights
  logging {
    cluster_log {
      enabled              = true
      log_group_name       = aws_cloudwatch_log_group.eks.name
      cloudwatch_log_group_class = "STANDARD"
    }
  }
  
  # Auto-scaling
  auto_scaling_config {
    min_size     = 3
    max_size     = 20
    desired_size = 10
  }
}

# Node group (auto-scaling)
resource "aws_eks_node_group" "omium" {
  cluster_name    = aws_eks_cluster.omium.name
  node_group_name = "omium-nodes"
  node_role_arn   = aws_iam_role.node_role.arn
  subnet_ids      = var.subnet_ids
  
  scaling_config {
    min_size     = 3
    max_size     = 30
    desired_size = 10
  }
  
  instance_types = ["t3.xlarge"]  # 4vCPU, 16GB RAM
  capacity_type  = "ON_DEMAND"     # For critical workloads
  
  # Spot instances for non-critical (cheaper)
  spot_price = "0.15"  # Adjust based on region
  
  disk_size = 100
  
  tags = {
    Environment = "production"
    Managed_by  = "terraform"
  }
}
```

**Kubernetes Deployment Example (Checkpoint Manager):**

```yaml
# checkpoint-manager-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: checkpoint-manager
  namespace: omium
spec:
  replicas: 3
  revisionHistoryLimit: 10
  
  selector:
    matchLabels:
      app: checkpoint-manager
  
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
      maxSurge: 1
  
  template:
    metadata:
      labels:
        app: checkpoint-manager
        version: v1
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8080"
        prometheus.io/path: "/metrics"
    
    spec:
      serviceAccountName: checkpoint-manager
      
      affinity:
        # Spread across different nodes
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - checkpoint-manager
              topologyKey: kubernetes.io/hostname
      
      containers:
      - name: checkpoint-manager
        image: 123456789.dkr.ecr.us-east-1.amazonaws.com/omium/checkpoint-manager:v1.0.0
        imagePullPolicy: IfNotPresent
        
        ports:
        - name: grpc
          containerPort: 7001
        - name: metrics
          containerPort: 8080
        
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: LOG_LEVEL
          value: "info"
        - name: POSTGRES_HOST
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: host
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: password
        
        resources:
          requests:
            cpu: 500m
            memory: 1Gi
          limits:
            cpu: 2000m
            memory: 4Gi
        
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 2
          failureThreshold: 2
        
        securityContext:
          runAsNonRoot: true
          runAsUser: 1000
          readOnlyRootFilesystem: true
          allowPrivilegeEscalation: false
          capabilities:
            drop:
            - ALL
      
      securityContext:
        fsGroup: 2000
      
      terminationGracePeriodSeconds: 30

---
apiVersion: v1
kind: Service
metadata:
  name: checkpoint-manager
  namespace: omium
spec:
  selector:
    app: checkpoint-manager
  type: ClusterIP
  ports:
  - name: grpc
    port: 7001
    targetPort: 7001
    protocol: TCP
  - name: metrics
    port: 8080
    targetPort: 8080
    protocol: TCP

---
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: checkpoint-manager-pdb
  namespace: omium
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: checkpoint-manager
```

**Service Mesh (Istio):**
```yaml
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: checkpoint-manager
  namespace: omium
spec:
  hosts:
  - checkpoint-manager
  http:
  - match:
    - uri:
        prefix: /
    route:
    - destination:
        host: checkpoint-manager
        port:
          number: 7001
      weight: 100
    retries:
      attempts: 3
      perTryTimeout: 2s
    timeout: 10s

---
apiVersion: networking.istio.io/v1alpha3
kind: DestinationRule
metadata:
  name: checkpoint-manager
  namespace: omium
spec:
  host: checkpoint-manager
  trafficPolicy:
    connectionPool:
      http:
        h2UpgradePolicy: UPGRADE
        maxRequestsPerConnection: 100
    outlierDetection:
      consecutive5xxErrors: 5
      interval: 30s
      baseEjectionTime: 30s
      maxEjectionPercent: 50
```

---

### 2.4 DATA LAYER

**Why Multiple Databases?**

Each database serves a specific purpose:

| Database | Use Case | Why This One |
|----------|----------|-------------|
| **PostgreSQL (RDS)** | Structured metadata | ACID transactions, JSON support, full-text search |
| **MongoDB (DocumentDB)** | Flexible schemas | Semi-structured traces, configs, flexibility |
| **Redis** | Cache + sessions | Sub-millisecond latency, excellent for real-time |
| **S3** | Large objects | Infinite scalability, cheap storage, versioning |
| **Elasticsearch** | Log search | Full-text search, aggregations, analytics |
| **Timestream** | Metrics | Optimized for time-series, auto-scaling |

**PostgreSQL (RDS) Configuration:**

```hcl
# rds.tf
resource "aws_db_instance" "postgres" {
  identifier     = "omium-postgres"
  engine         = "postgres"
  engine_version = "15.3"
  instance_class = "db.r6i.xlarge"  # 4vCPU, 32GB RAM
  allocated_storage = 500  # GB
  
  # Multi-AZ for high availability
  multi_az = true
  
  # Backups
  backup_retention_period = 35
  backup_window           = "03:00-04:00"
  copy_tags_to_snapshot   = true
  
  # Performance Insights
  performance_insights_enabled = true
  monitoring_interval         = 60
  
  # Encryption
  storage_encrypted = true
  kms_key_id        = aws_kms_key.rds.arn
  
  # Network
  db_subnet_group_name   = aws_db_subnet_group.default.name
  publicly_accessible    = false
  vpc_security_group_ids = [aws_security_group.rds.id]
  
  # Deletion protection
  deletion_protection = true
  
  tags = {
    Name = "omium-postgres"
  }
}

# Read replica for analytics queries
resource "aws_db_instance" "postgres_replica" {
  identifier          = "omium-postgres-replica"
  replicate_source_db = aws_db_instance.postgres.identifier
  instance_class      = "db.r6i.large"  # Cheaper than primary
  skip_final_snapshot = false
  
  performance_insights_enabled = true
  
  tags = {
    Name = "omium-postgres-replica"
  }
}
```

**PostgreSQL Schema (Key Tables):**

```sql
-- Core execution tracking
CREATE TABLE executions (
    id UUID PRIMARY KEY,
    workflow_id UUID NOT NULL,
    tenant_id UUID NOT NULL,
    status VARCHAR(50),
    created_at TIMESTAMP,
    completed_at TIMESTAMP,
    INDEX idx_tenant_created (tenant_id, created_at)
);

CREATE TABLE checkpoints (
    id UUID PRIMARY KEY,
    execution_id UUID NOT NULL,
    agent_id UUID NOT NULL,
    checkpoint_name VARCHAR(255),
    state_size_bytes INT,
    state_blob_uri VARCHAR(1000),
    checksum VARCHAR(64),
    created_at TIMESTAMP,
    FOREIGN KEY (execution_id) REFERENCES executions(id),
    INDEX idx_exec_checkpoint (execution_id, checkpoint_name)
);

-- User & Tenant management
CREATE TABLE tenants (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    subscription_tier VARCHAR(50),
    created_at TIMESTAMP
);

CREATE TABLE users (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    email VARCHAR(255) UNIQUE,
    hashed_password VARCHAR(255),
    created_at TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id)
);

-- Audit logging
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    user_id UUID,
    action VARCHAR(100),
    resource_id UUID,
    changes JSONB,
    timestamp TIMESTAMP,
    INDEX idx_tenant_timestamp (tenant_id, timestamp)
);
```

**Redis Configuration (ElastiCache):**

```hcl
# redis.tf
resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "omium-redis"
  engine               = "redis"
  node_type            = "cache.r6g.xlarge"  # 16GB
  num_cache_nodes      = 3  # Multi-AZ
  parameter_group_name = "default.redis7"
  port                 = 6379
  
  # High availability
  automatic_failover_enabled = true
  multi_az_enabled           = true
  
  # Encryption
  transit_encryption_enabled = true
  at_rest_encryption_enabled = true
  auth_token                 = random_password.redis_auth.result
  
  # Backup
  snapshot_retention_limit = 35
  snapshot_window          = "03:00-05:00"
  
  # Subnet group
  subnet_group_name = aws_elasticache_subnet_group.default.name
  security_group_ids = [aws_security_group.redis.id]
  
  log_delivery_configuration {
    destination      = aws_cloudwatch_log_group.redis_slow.name
    destination_type = "cloudwatch-logs"
    log_format       = "json"
    log_type         = "slow-log"
  }
  
  tags = {
    Name = "omium-redis"
  }
}
```

---

### 2.5 INFRASTRUCTURE LAYER

**Message Queue (Kafka):**

Not managed by AWS - run on separate EC2 instances for full control

```hcl
# kafka.tf
resource "aws_instance" "kafka_broker" {
  count                = 3
  ami                  = data.aws_ami.ubuntu.id
  instance_type        = "t3.2xlarge"
  subnet_id            = var.subnet_ids[count.index % 3]
  iam_instance_profile = aws_iam_instance_profile.kafka.name
  
  vpc_security_group_ids = [aws_security_group.kafka.id]
  
  root_block_device {
    volume_size = 500
    volume_type = "gp3"
  }
  
  user_data = base64encode(file("${path.module}/kafka-init.sh"))
  
  tags = {
    Name = "kafka-broker-${count.index + 1}"
  }
}
```

**CI/CD Pipeline (GitHub Actions):**

```yaml
# .github/workflows/deploy.yml
name: Deploy Omium

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  AWS_REGION: us-east-1
  ECR_REGISTRY: 123456789.dkr.ecr.us-east-1.amazonaws.com

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Run tests
      run: |
        cd core-services
        for service in checkpoint-manager consensus-coordinator execution-engine; do
          cd $service
          pytest tests/
          cd ..
        done
  
  build:
    needs: test
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: read
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v2
      with:
        role-to-assume: arn:aws:iam::123456789:role/github-actions
        aws-region: ${{ env.AWS_REGION }}
    
    - name: Login to ECR
      run: |
        aws ecr get-login-password --region ${{ env.AWS_REGION }} | \
        docker login --username AWS --password-stdin ${{ env.ECR_REGISTRY }}
    
    - name: Build and push images
      run: |
        for service in checkpoint-manager consensus-coordinator execution-engine; do
          docker build -t ${{ env.ECR_REGISTRY }}/omium/$service:${{ github.sha }} \
            core-services/$service/
          docker push ${{ env.ECR_REGISTRY }}/omium/$service:${{ github.sha }}
        done
  
  deploy-staging:
    needs: build
    runs-on: ubuntu-latest
    environment: staging
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v2
      with:
        role-to-assume: arn:aws:iam::123456789:role/github-actions
        aws-region: ${{ env.AWS_REGION }}
    
    - name: Update kubeconfig
      run: |
        aws eks update-kubeconfig --name omium-staging --region ${{ env.AWS_REGION }}
    
    - name: Deploy with Helm
      run: |
        helm repo add omium https://charts.omium.io
        helm upgrade --install omium-staging omium/platform \
          --namespace omium-staging \
          --values values-staging.yaml \
          --set image.tag=${{ github.sha }} \
          --wait
    
    - name: Run smoke tests
      run: |
        kubectl port-forward -n omium-staging svc/api-gateway 8000:80 &
        sleep 5
        pytest tests/smoke_tests.py
```

---

## 3. DEPLOYMENT ARCHITECTURE (AWS + Digital Ocean)

### 3.1 AWS Deployment

**Regions & Availability:**
```
Primary Region: us-east-1 (N. Virginia)
├─ AZ-1: us-east-1a
├─ AZ-2: us-east-1b
└─ AZ-3: us-east-1c

All critical services deployed across 3 AZs
```

**Component Placement:**

| Component | Service | AWS Placement | Instance Type | Count |
|-----------|---------|---------------|---------------|-------|
| **Frontend** | React apps | S3 + CloudFront | N/A | Global CDN |
| **API Gateway** | Kong | EC2 (public subnet) | t3.xlarge | 2 |
| **Auth Service** | Python/FastAPI | EC2 (public subnet) | t3.large | 2 |
| **EKS Control Plane** | Kubernetes | AWS Managed | N/A | 1 |
| **EKS Nodes** | Worker nodes | EC2 (private subnet) | t3.xlarge | 10 (auto-scale 3-30) |
| **RDS PostgreSQL** | Primary DB | Multi-AZ RDS | db.r6i.xlarge | 1 primary + 1 read replica |
| **DocumentDB** | Traces/configs | Multi-AZ DocumentDB | 3-node cluster | 1 cluster |
| **ElastiCache Redis** | Cache | Multi-AZ ElastiCache | cache.r6g.xlarge | 3 nodes |
| **S3** | Object storage | Multi-region | N/A | 1 bucket (replicated) |
| **Elasticsearch** | Logs | Multi-AZ ES | 3-node cluster | 1 cluster |
| **Timestream** | Metrics | Managed AWS | N/A | 1 |
| **Kafka** | Message queue | EC2 (private subnet) | t3.2xlarge | 3 brokers |

**Network Diagram:**
```
┌─────────────────────────────────────────────────────────────────┐
│ AWS VPC (10.0.0.0/16)                                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Internet Gateway                                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│           ↓                                                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ AWS ALB (Application Load Balancer)                      │  │
│  │ ├─ Listener: 443 (HTTPS)                                │  │
│  │ ├─ Target Group 1: Kong (port 8000)                     │  │
│  │ └─ Target Group 2: Auth (port 3000)                     │  │
│  └──────────────────────────────────────────────────────────┘  │
│           ↓                                                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ PUBLIC SUBNETS (NAT Gateway)                             │  │
│  │ ├─ Public Subnet 1a (10.0.1.0/24)                       │  │
│  │ │  ├─ EC2: Kong + Auth #1                               │  │
│  │ │  └─ NAT Gateway                                        │  │
│  │ ├─ Public Subnet 1b (10.0.2.0/24)                       │  │
│  │ │  ├─ EC2: Kong + Auth #2                               │  │
│  │ │  └─ NAT Gateway                                        │  │
│  │ └─ Public Subnet 1c (10.0.3.0/24)                       │  │
│  │    └─ NAT Gateway (for high availability)                │  │
│  └──────────────────────────────────────────────────────────┘  │
│           ↓ (Internal routing)                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ PRIVATE SUBNETS (No direct internet access)             │  │
│  │ ├─ Private Subnet 1a (10.0.11.0/24)                     │  │
│  │ │  └─ EKS Worker Nodes (10+ pods)                       │  │
│  │ ├─ Private Subnet 1b (10.0.12.0/24)                     │  │
│  │ │  └─ EKS Worker Nodes (10+ pods)                       │  │
│  │ └─ Private Subnet 1c (10.0.13.0/24)                     │  │
│  │    └─ EKS Worker Nodes (10+ pods)                       │  │
│  └──────────────────────────────────────────────────────────┘  │
│           ↓                                                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ DATABASE SUBNETS (Multi-AZ)                             │  │
│  │ ├─ DB Subnet 1a: RDS Primary, ElastiCache Node 1        │  │
│  │ ├─ DB Subnet 1b: RDS Replica, ElastiCache Node 2        │  │
│  │ └─ DB Subnet 1c: DocumentDB, ElastiCache Node 3         │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ KAFKA CLUSTER (Private Subnets)                          │  │
│  │ ├─ EC2 Kafka Broker 1 (10.0.11.10)                      │  │
│  │ ├─ EC2 Kafka Broker 2 (10.0.12.10)                      │  │
│  │ └─ EC2 Kafka Broker 3 (10.0.13.10)                      │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

**Security Groups:**

```hcl
# ALB Security Group
resource "aws_security_group" "alb" {
  name = "omium-alb"
  
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  # HTTPS from internet
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Backend EC2 Security Group
resource "aws_security_group" "backend" {
  name = "omium-backend"
  
  ingress {
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]  # From ALB only
  }
  
  ingress {
    from_port       = 3000
    to_port         = 3000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]  # To anywhere
  }
}

# EKS Security Group
resource "aws_security_group" "eks" {
  name = "omium-eks"
  
  ingress {
    from_port       = 0
    to_port         = 65535
    protocol        = "tcp"
    security_groups = [aws_security_group.eks.id]  # Pod-to-pod communication
  }
  
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]  # From VPC
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
```

---

### 3.2 Digital Ocean Deployment (AI Compute)

**Why Digital Ocean for AI?**
- Simpler API than AWS
- Better for compute-heavy workloads
- Private networking between AWS & DO
- Cost-effective for GPU instances (if needed later)

**Digital Ocean Architecture:**

```
┌─────────────────────────────────────┐
│ Digital Ocean                        │
├─────────────────────────────────────┤
│                                      │
│  Execution Engine - AI Compute       │
│  ├─ 2-4 High-Memory Droplets (32GB) │
│  │  ├─ Python 3.11                  │
│  │  ├─ LLM SDKs (OpenAI, Anthropic) │
│  │  └─ Isolated inference            │
│  │                                   │
│  Recovery Orchestrator               │
│  ├─ 1-2 Droplets (16GB)             │
│  │  ├─ ML models for analysis       │
│  │  └─ Root cause analysis          │
│  │                                   │
│  ┌─────────────────────────────────┐│
│  │ Digital Ocean Managed Postgres   ││ (optional secondary)
│  │ ├─ Read-only replica             ││
│  │ └─ Backup from AWS               ││
│  └─────────────────────────────────┘│
│                                      │
└─────────────────────────────────────┘
```

**Network Bridge (AWS ↔ Digital Ocean):**

```
AWS VPC (10.0.0.0/16)
    ↓
AWS VPN Gateway / AWS Site-to-Site VPN
    ↓ (IPsec tunnel)
    ↓
Digital Ocean Private Network
    ↓
DO Droplets (Internal IPs: 10.132.0.0/16)
```

**Terraform for Digital Ocean:**

```hcl
# do.tf
terraform {
  required_providers {
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.0"
    }
  }
}

variable "do_token" {
  description = "Digital Ocean API token"
  sensitive   = true
}

provider "digitalocean" {
  token = var.do_token
}

# VPC for private networking
resource "digitalocean_vpc" "omium" {
  name   = "omium-vpc"
  region = "nyc3"
}

# Execution Engine Droplets
resource "digitalocean_droplet" "execution_engine" {
  count              = 2
  name               = "execution-engine-${count.index + 1}"
  image              = "ubuntu-22-04-x64"
  region             = "nyc3"
  size               = "s-32gb"  # 32GB RAM, 8 vCPU
  monitoring         = true
  private_networking = true
  vpc_uuid           = digitalocean_vpc.omium.id
  
  ssh_keys = [digitalocean_ssh_key.main.id]
  
  user_data = file("${path.module}/execution-engine-init.sh")
  
  tags = ["omium", "execution-engine", "production"]
}

# Recovery Orchestrator Droplets
resource "digitalocean_droplet" "recovery_orchestrator" {
  count              = 1
  name               = "recovery-orchestrator-${count.index + 1}"
  image              = "ubuntu-22-04-x64"
  region             = "nyc3"
  size               = "s-16gb"  # 16GB RAM, 4 vCPU
  monitoring         = true
  private_networking = true
  vpc_uuid           = digitalocean_vpc.omium.id
  
  ssh_keys = [digitalocean_ssh_key.main.id]
  
  user_data = file("${path.module}/recovery-orchestrator-init.sh")
  
  tags = ["omium", "recovery-orchestrator", "production"]
}

# Load Balancer
resource "digitalocean_loadbalancer" "omium" {
  name   = "omium-lb"
  region = "nyc3"
  
  forwarding_rule {
    entry_protocol  = "tcp"
    entry_port      = 7001
    target_protocol = "tcp"
    target_port     = 7001
  }
  
  health_check {
    protocol            = "http"
    port                = 8080
    path                = "/health"
    check_interval_seconds   = 10
    response_timeout_seconds = 5
    healthy_threshold        = 3
    unhealthy_threshold      = 5
  }
  
  sticky_sessions {
    type               = "none"
  }
  
  # Target droplets
  droplet_ids = concat(
    digitalocean_droplet.execution_engine[*].id,
    digitalocean_droplet.recovery_orchestrator[*].id
  )
}
```

**VPN Connection Setup:**

```bash
#!/bin/bash
# setup-vpn.sh - Connect AWS to Digital Ocean

# AWS side: Create VPN connection
aws ec2 create-vpn-connection \
  --type ipsec.1 \
  --customer-gateway-id cgw-xxx \
  --vpn-gateway-id vgw-xxx

# Digital Ocean side: Configure Droplet as VPN endpoint
sudo apt-get update
sudo apt-get install -y strongswan
sudo systemctl start strongswan
sudo systemctl enable strongswan

# Configure IPsec tunnel between VPCs
# (Details depend on AWS VPN config)
```

---

## 4. COMMUNICATION PATTERNS

### 4.1 Service-to-Service Communication

**Protocol Decision:**

| Protocol | Use Case | Performance | Complexity |
|----------|----------|-------------|-----------|
| **REST (HTTP/2)** | External APIs, simpler services | Medium | Low |
| **gRPC** | High-performance inter-service | HIGH | Medium |
| **Kafka** | Event streaming, async | Async/fire-and-forget | Medium |
| **WebSocket** | Real-time dashboards | Real-time | Medium |

**Our Decision:**
- **gRPC**: For inter-microservice (execution-engine ↔ checkpoint-manager)
- **REST**: For external APIs (frontend ↔ backend)
- **Kafka**: For event streaming (async operations)
- **WebSocket**: For dashboard real-time updates

**gRPC Service Definition:**

```protobuf
// checkpoint.proto
syntax = "proto3";

package omium.checkpoint;

service CheckpointService {
  rpc CreateCheckpoint(CreateCheckpointRequest) returns (CreateCheckpointResponse);
  rpc GetCheckpoint(GetCheckpointRequest) returns (GetCheckpointResponse);
  rpc RollbackToCheckpoint(RollbackRequest) returns (RollbackResponse);
}

message CreateCheckpointRequest {
  string execution_id = 1;
  string agent_id = 2;
  string checkpoint_name = 3;
  bytes state = 4;
  map<string, string> metadata = 5;
}

message CreateCheckpointResponse {
  string checkpoint_id = 1;
  int64 size_bytes = 2;
  string checksum = 3;
}
```

**Kafka Topic Schema:**

```json
{
  "topic": "execution_events",
  "partitions": 10,
  "replication_factor": 3,
  "retention_ms": 604800000,
  "messages": [
    {
      "type": "execution_started",
      "execution_id": "exec_12345",
      "workflow_id": "flow_xxx",
      "timestamp": 1234567890000,
      "agents": ["agent_a", "agent_b"]
    },
    {
      "type": "checkpoint_created",
      "execution_id": "exec_12345",
      "checkpoint_name": "step_1",
      "agent_id": "agent_a",
      "timestamp": 1234567895000
    },
    {
      "type": "failure_detected",
      "execution_id": "exec_12345",
      "error": "hallucination",
      "timestamp": 1234567900000
    }
  ]
}
```

---

## 5. DATA FLOW DIAGRAMS

### 5.1 Execution Data Flow

```
┌──────────────────┐
│  Frontend User   │
│  Submits Agent   │
└────────┬─────────┘
         │ REST API
         ↓
┌──────────────────┐
│ API Gateway      │
│ (Kong on EC2)    │
└────────┬─────────┘
         │ Authenticate + Route
         ↓
┌──────────────────┐
│ Workflow Manager │
│ (EKS)            │
└────────┬─────────┘
         │ Parse YAML/JSON
         ↓
┌──────────────────┐
│ Execution Engine │
│ (EKS or DO)      │
└────────┬─────────┘
         │ Load agents + LLM SDKs
         ↓
┌──────────────────┐
│ Checkpoint Mgr   │
│ (EKS)            │
└────────┬─────────┘
         │ Pre-execution checkpoint
         ↓
┌──────────────────┐
│ Agent Runtime    │
│ (CrewAI/LG)      │
└────────┬─────────┘
         │ Execute
         ↓
┌──────────────────┐
│ LLM API Call     │
│ (OpenAI, etc)    │
└────────┬─────────┘
         │ LLM Response
         ↓
┌──────────────────┐
│ Post-condition   │
│ Check            │
└────────┬─────────┘
         │ Valid?
         ├─YES────→ Checkpoint saved (PostgreSQL + S3)
         │          ↓
         │          Consensus broker notified (Kafka)
         │          ↓
         │          Tracing logged (ElasticSearch)
         │
         └─NO─────→ Trigger failure recovery
                    ↓
                    Recovery Orchestrator
                    ↓
                    Root cause analysis (ML)
                    ↓
                    Suggest fixes
                    ↓
                    Human review
                    ↓
                    Retry from checkpoint
```

---

## 6. SERVICE DEPENDENCIES

```
Execution Flow Dependencies:

API Gateway
  ↓
Auth Service ← → Authorization Service
  ↓
Workflow Manager
  ↓
Execution Engine ← → Consensus Coordinator
  ↓                    ↓
Checkpoint Manager ← → Tracing Service
  ↓                    ↓
Policy Engine   ← → Analytics Engine
  ↓
Recovery Orchestrator

Data Dependencies:

All Services → PostgreSQL (metadata)
Execution Engine ↔ MongoDB (traces)
Consensus Coordinator → Redis (live state)
Analytics Engine → Timestream (metrics)
Logging → Elasticsearch
Async Events → Kafka
```

---

## 7. SCALABILITY & PERFORMANCE TARGETS

| Component | Max Load | Scaling Method | Target Latency |
|-----------|----------|-----------------|-----------------|
| **Frontend** | 10K concurrent users | CloudFront CDN, caching | <200ms |
| **API Gateway** | 5K req/sec | ALB auto-scaling, horizontal | <50ms |
| **EKS Services** | 1K+ concurrent workflows | Horizontal pod autoscaler | <500ms |
| **PostgreSQL** | 10K queries/sec | Read replicas, connection pooling | <10ms |
| **Redis** | 100K ops/sec | Cluster mode, sharding | <1ms |
| **Kafka** | 1M messages/sec | Partitioning, brokers | <100ms end-to-end |

---

## 8. DISASTER RECOVERY & HA

**RPO (Recovery Point Objective):** 1 hour  
**RTO (Recovery Time Objective):** 4 hours

**Backups:**
- PostgreSQL: Continuous, 35-day retention
- S3: Versioning enabled, cross-region replication
- Kafka: 7-day retention (replay capability)
- Kubernetes configs: Git (GitHub)

**Multi-Region Failover (Future):**
- us-east-1 (Primary)
- eu-west-1 (Standby) - can activate in 4 hours

---

## 9. SECURITY ARCHITECTURE

**Layers:**

```
1. Network Security
   ├─ VPC isolation
   ├─ Security groups
   ├─ NACLs
   └─ WAF (AWS)

2. Transport Security
   ├─ TLS 1.3 everywhere
   ├─ mTLS in service mesh
   └─ VPN to Digital Ocean

3. Application Security
   ├─ OAuth2 / SAML
   ├─ JWT tokens
   ├─ RBAC
   └─ Rate limiting

4. Data Security
   ├─ AES-256 encryption at rest
   ├─ Encryption in transit
   └─ Secrets rotation

5. Audit & Compliance
   ├─ CloudTrail logging
   ├─ IAM policies
   ├─ SOC 2 / HIPAA ready
   └─ Audit trail in PostgreSQL
```

---

## 10. IMPLEMENTATION PRIORITIES

**Phase 1 (Weeks 1-4): Foundation**
- Set up AWS infrastructure (VPC, RDS, ElastiCache)
- Build API Gateway + Auth service
- Deploy basic EKS cluster

**Phase 2 (Weeks 5-8): Core Services**
- Checkpoint Manager
- Execution Engine (Python)
- Basic Tracing Service

**Phase 3 (Weeks 9-12): Advanced Features**
- Consensus Coordinator (Rust)
- Recovery Orchestrator
- Analytics Engine
- Digital Ocean integration

**Phase 4 (Weeks 13-16): Operations**
- CI/CD pipeline
- Monitoring & alerting
- Disaster recovery setup
- Security hardening

---

**Document End**

This HLD is production-ready for immediate implementation. All AWS services are configured for high availability, security, and cost optimization.

# Let's get back to what we were into the technical

*Converted from PDF: Let's get back to what we were into the technical.pdf*

---

## Page 1

Perfect! I've created a comprehensive HLD (High-Level Design) document. Now let me
summarize the key tech stack decisions for you:
React 18 + TypeScript → Vite (build) → S3 + CloudFront (CDN)
├─ State: Redux Toolkit
├─ Real-time: WebSocket (Socket.io)
├─ UI: Tailwind CSS + shadcn/ui
└─ Deploy: GitHub Actions → S3 → CloudFront
AWS EC2 (t3.xlarge x2)
├─ API Gateway: Kong (reverse proxy + plugins)
├─ Auth Service: Python/FastAPI (OAuth2, SAML, JWT, MFA)
├─ Load Balancer: AWS ALB (SSL/TLS termination)
└─ Deploy: Docker + GitHub Actions
Let's get back to what we were into the technical
thing. I analyze the things you said me. Create me
the HLD Design of the platform also tell me what is
the best tech stacks to proceed with. And to tell
you, the frontend will be deployed in AWS +
Cloudfront, Backend in EC2 and we have digital
ocean droplet as well for AI things, I know things
are little vague in the deployment. You have to
clear things in that as well.
OMIUM TECH STACK SUMMARY
FRONTEND LAYER
BACKEND LAYER (API Gateway + Auth)


## Page 2

AWS EKS Cluster (Kubernetes)
├─ Checkpoint Manager → Go (gRPC)
├─ Consensus Coordinator → Rust (Tokio, memory-safe)
├─ Execution Engine → Python (FastAPI, LLM SDKs)
├─ Recovery Orchestrator → Python (root cause analysis)
├─ Tracing Service → Go (OpenTelemetry)
├─ Policy Engine → Go (OPA/Rego)
├─ Workflow Manager → Python (YAML orchestration)
└─ Analytics Engine → Python (Pandas, SQL)
Service Mesh: Istio (mTLS, traffic management)
Event Queue: Kafka (3 brokers on EC2)
├─ PostgreSQL → AWS RDS (Multi-AZ, read replicas)
├─ MongoDB → AWS DocumentDB (flexible schemas)
├─ Cache → AWS ElastiCache (Redis, Multi-AZ)
├─ Object Storage → AWS S3 (versions, encryption)
├─ Logs → AWS Elasticsearch (full-text search)
├─ Metrics → AWS Timestream (time-series optimized)
└─ Connection Pooling → PgBouncer on EC2
Digital Ocean Droplets (high-memory)
├─ Execution Engine replica → 2-4 x 32GB droplets
├─ Recovery Orchestrator → 1-2 x 16GB droplets
├─ Connection: Private VPN + Kafka bridge to AWS
└─ Use case: Heavy LLM inference, GPU (future)
├─ Orchestration: AWS EKS + Kubernetes
├─ IaC: Terraform (all AWS resources)
├─ Package Management: Helm charts
├─ CI/CD: GitHub Actions → ECR → EKS
├─ Monitoring: CloudWatch + Prometheus + Grafana
├─ Security: KMS, Secrets Manager, IAM, WAF
└─ VPC: Multi-AZ (3 AZs), private/public subnets
CORE SERVICES LAYER (AWS EKS)
DATA LAYER (AWS Managed Services)
DIGITAL OCEAN (AI Compute)
INFRASTRUCTURE


## Page 3

WHY THIS TECH STACK?
Go for Performance-Critical Services
Compilation to binary
Goroutines (lightweight concurrency)
No GC pauses
Small Docker images (~20MB)
✅ Used by: Uber, CloudFlare, Docker
Rust for Correctness & Safety
Memory safety without GC
No null pointer dereferences
No data races (compile-time guaranteed)
Similar performance to C++
✅ Used by: AWS Firecracker, Cloudflare Workers
Python for Rapid Development
Massive ecosystem (NumPy, Pandas, scikit-learn)
LLM SDKs well-developed (OpenAI, Anthropic)
Easy to iterate and debug
FastAPI: Modern, performant async web framework
✅ Used by: Netflix, Spotify, Uber
AWS EKS (not self-managed K8s)
AWS manages control plane
Deep AWS integration (IAM, VPC, ALB, KMS)
No control plane maintenance
Kubernetes API compatibility
✅ Industry standard for enterprises
Digital Ocean Complement
Simpler API than AWS
Better for compute-heavy workloads
Private networking to AWS
Cost-effective alternative for specific workloads


## Page 4

PRODUCTION DEPLOYMENT (AWS us-east-1):
┌─ FRONTEND ─────────────────────────────────────────┐
│ React apps built with Vite                          │
│ Deployed to S3 bucket (versioned)                   │
│ Cached globally via CloudFront CDN                  │
│ SSL/TLS at edge                                     │
└────────────────────────────────────────────────────┘
┌─ BACKEND (EC2) ────────────────────────────────────┐
│ 2x t3.xlarge instances (multi-AZ)                   │
│ ALB in front (load balancing, SSL)                  │
│ Kong API Gateway + Auth Service                     │
│ All behind NAT Gateway                              │
└────────────────────────────────────────────────────┘
┌─ CORE SERVICES (EKS) ──────────────────────────────┐
│ Kubernetes cluster (AWS managed control plane)      │
│ 10 worker nodes (auto-scale 3-30)                   │
│ 8 microservices (Go, Rust, Python)                  │
│ Istio service mesh (mTLS between pods)              │
│ Kafka cluster on EC2 (3 brokers)                    │
└────────────────────────────────────────────────────┘
┌─ DATA LAYER (AWS Managed) ─────────────────────────┐
│ RDS PostgreSQL (Multi-AZ)                           │
│ DocumentDB (MongoDB API)                            │
│ ElastiCache Redis (Multi-AZ)                        │
│ S3 (versioned, encrypted)                           │
│ Elasticsearch (log indexing)                        │
│ Timestream (metrics)                                │
└────────────────────────────────────────────────────┘
┌─ DIGITAL OCEAN (Optional AI Compute) ──────────────┐
│ 2-4 high-memory droplets (32GB each)                │
│ For heavy execution engine workloads                │
│ Connected via VPN to AWS                            │
│ Kafka bridge for event streaming                    │
└────────────────────────────────────────────────────┘
You now have:
DEPLOYMENT SUMMARY
NEXT STEPS
1. ✅ Complete folder structure
2. ✅ Detailed tech stack decisions with justifications
3. ✅ AWS architecture (with 3 AZs, multi-region ready)
4. ✅ Digital Ocean integration
5. ✅ Security, HA, and disaster recovery planned


## Page 5

What's downloaded:
Ready to proceed with:
What do you want to tackle next?
⁂
6. ✅ Implementation roadmap (4 phases)
code_file:342 - Full 30+ page Product Spec (Omium-Full-Spec.md)
code_file:394 - Complete HLD & Tech Stack (Omium-HLD-Architecture.md)
1. LLD (Low-Level Design) - Detailed API specs, database schemas, gRPC definitions
2. Deployment automation - Terraform modules, Helm charts, CI/CD pipelines
3. Prototype/POC - Build the MVP checkpoint system as proof of concept
4. Infrastructure setup - Spin up AWS VPC, EKS, RDS, etc.
1. https://ieeexplore.ieee.org/document/11157964/
2. https://www.mdpi.com/2079-9292/13/2/285/pdf?version=1704708410
3. http://arxiv.org/pdf/2503.21096.pdf
4. https://arxiv.org/pdf/2305.13933.pdf
5. https://arxiv.org/pdf/2104.02423.pdf
6. https://www.qovery.com/blog/10-best-practices-for-optimizing-kubernetes-on-aws
7. https://distantjob.com/blog/best-programming-languages-for-microservices/
8. https://www.simform.com/blog/multi-cloud-architecture/
9. https://www.sedai.io/blog/guide-amazon-eks-managed-kubernetes-aws
10. https://www.linkedin.com/posts/jai-vine_rust-vs-go-the-backend-showdown-heating-activity-7359165
071660400642-Rt-m
11. https://www.perfectiongeeks.com/multi-cloud-architecture-designs
12. https://journalwjarr.com/node/1847
13. https://aws.amazon.com/blogs/containers/saas-deployment-architectures-with-amazon-eks/
14. https://www.kansoftware.com/best-tech-stack-for-mobile-app-development-2025/
15. https://www.infoq.com/presentations/event-driven-multi-cloud/
16. https://cast.ai/blog/eks-cost-optimization/
17. https://ieeexplore.ieee.org/document/10575628/
18. https://www.ijsat.org/research-paper.php?id=2809
19. https://www.semanticscholar.org/paper/4d2bcc8d3c22a40ab8f5725d5807d99dd3d3708b
20. http://arxiv.org/pdf/2407.01620.pdf
21. https://arxiv.org/pdf/2503.04815.pdf
22. http://arxiv.org/pdf/2410.10655.pdf
23. https://arxiv.org/pdf/2501.16143.pdf


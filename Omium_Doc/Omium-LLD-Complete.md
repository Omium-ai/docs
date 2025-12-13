# OMIUM: Low-Level Design (LLD)
## Detailed API Specs, Database Schemas, gRPC Definitions

**Version:** 1.0  
**Date:** November 12, 2025  
**Status:** Complete LLD for Implementation

---

## TABLE OF CONTENTS

1. Database Schema (Complete)
2. API Specifications (REST)
3. gRPC Service Definitions
4. Data Models & Types
5. Error Handling & Response Codes
6. Authentication & Authorization Flow
7. Service Interactions (Detailed)
8. Code Examples (Implementation)

---

## 1. DATABASE SCHEMA (COMPLETE)

### 1.1 PostgreSQL Schema

#### **Tenants & Users**

```sql
-- Tenants (Multi-tenant support)
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    subscription_tier VARCHAR(50) NOT NULL DEFAULT 'starter',
    subscription_status VARCHAR(50) NOT NULL DEFAULT 'active',
    stripe_customer_id VARCHAR(255),
    
    -- Limits
    max_checkpoints_per_month INT DEFAULT 50000,
    max_concurrent_executions INT DEFAULT 10,
    
    -- Billing
    billing_email VARCHAR(255),
    billing_address JSONB,
    
    -- Metadata
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMP,
    
    CONSTRAINT valid_tier CHECK (subscription_tier IN ('starter', 'professional', 'enterprise'))
);

CREATE INDEX idx_tenants_slug ON tenants(slug);
CREATE INDEX idx_tenants_status ON tenants(subscription_status);

-- Users
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    email VARCHAR(255) NOT NULL,
    email_verified BOOLEAN DEFAULT FALSE,
    hashed_password VARCHAR(255),
    
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    
    -- Auth
    auth_provider VARCHAR(50) DEFAULT 'local',
    oauth_provider_id VARCHAR(255),
    mfa_enabled BOOLEAN DEFAULT FALSE,
    mfa_secret VARCHAR(255),
    
    -- Status
    status VARCHAR(50) DEFAULT 'active',
    last_login_at TIMESTAMP,
    
    -- Metadata
    avatar_url VARCHAR(500),
    timezone VARCHAR(50) DEFAULT 'UTC',
    preferences JSONB DEFAULT '{}',
    
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    UNIQUE(email),
    UNIQUE(tenant_id, email),
    CONSTRAINT valid_auth_provider CHECK (auth_provider IN ('local', 'google', 'github', 'saml'))
);

CREATE INDEX idx_users_tenant ON users(tenant_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_status ON users(status);

-- Roles
CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    name VARCHAR(100) NOT NULL,
    description TEXT,
    permissions JSONB NOT NULL DEFAULT '[]',
    
    is_system_role BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    UNIQUE(tenant_id, name)
);

CREATE INDEX idx_roles_tenant ON roles(tenant_id);

-- User Roles (Many-to-Many)
CREATE TABLE user_roles (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    
    granted_by UUID REFERENCES users(id),
    granted_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    PRIMARY KEY (user_id, role_id)
);

CREATE INDEX idx_user_roles_user ON user_roles(user_id);
CREATE INDEX idx_user_roles_role ON user_roles(role_id);

-- API Keys (for programmatic access)
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    
    name VARCHAR(255) NOT NULL,
    key_hash VARCHAR(255) NOT NULL UNIQUE,
    key_prefix VARCHAR(20) NOT NULL,
    
    permissions JSONB DEFAULT '[]',
    
    last_used_at TIMESTAMP,
    expires_at TIMESTAMP,
    
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    revoked_at TIMESTAMP,
    
    CONSTRAINT valid_expiry CHECK (expires_at IS NULL OR expires_at > created_at)
);

CREATE INDEX idx_api_keys_tenant ON api_keys(tenant_id);
CREATE INDEX idx_api_keys_hash ON api_keys(key_hash);
CREATE INDEX idx_api_keys_prefix ON api_keys(key_prefix);
```

#### **Executions & Workflows**

```sql
-- Workflows (definitions)
CREATE TABLE workflows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    created_by UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Workflow definition
    definition JSONB NOT NULL,
    version INT NOT NULL DEFAULT 1,
    
    -- Configuration
    config JSONB DEFAULT '{}',
    
    -- Status
    status VARCHAR(50) DEFAULT 'draft',
    published_at TIMESTAMP,
    
    -- Tags
    tags TEXT[] DEFAULT '{}',
    
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMP,
    
    CONSTRAINT valid_status CHECK (status IN ('draft', 'published', 'archived'))
);

CREATE INDEX idx_workflows_tenant ON workflows(tenant_id);
CREATE INDEX idx_workflows_status ON workflows(status);
CREATE INDEX idx_workflows_tags ON workflows USING GIN(tags);

-- Executions (workflow runs)
CREATE TABLE executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    workflow_id UUID NOT NULL REFERENCES workflows(id) ON DELETE RESTRICT,
    
    -- Execution metadata
    triggered_by UUID REFERENCES users(id),
    trigger_type VARCHAR(50) DEFAULT 'manual',
    
    -- Status tracking
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    -- Results
    result JSONB,
    error TEXT,
    
    -- Checkpoint tracking
    current_checkpoint VARCHAR(255),
    last_successful_checkpoint VARCHAR(255),
    
    -- Metadata
    input_params JSONB,
    output JSONB,
    metadata JSONB DEFAULT '{}',
    
    -- Performance
    duration_ms INT,
    checkpoint_count INT DEFAULT 0,
    retry_count INT DEFAULT 0,
    
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    CONSTRAINT valid_status CHECK (status IN (
        'pending', 'running', 'paused', 'completed', 
        'failed', 'rolled_back', 'cancelled'
    )),
    CONSTRAINT valid_trigger CHECK (trigger_type IN (
        'manual', 'api', 'scheduled', 'webhook', 'event'
    ))
);

CREATE INDEX idx_executions_tenant ON executions(tenant_id);
CREATE INDEX idx_executions_workflow ON executions(workflow_id);
CREATE INDEX idx_executions_status ON executions(status);
CREATE INDEX idx_executions_started ON executions(started_at);

-- Partition executions by month for performance
CREATE TABLE executions_2025_11 PARTITION OF executions
FOR VALUES FROM ('2025-11-01') TO ('2025-12-01');

CREATE TABLE executions_2025_12 PARTITION OF executions
FOR VALUES FROM ('2025-12-01') TO ('2026-01-01');

-- Agents (execution components)
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id UUID NOT NULL REFERENCES executions(id) ON DELETE CASCADE,
    
    name VARCHAR(255) NOT NULL,
    agent_type VARCHAR(100) NOT NULL,
    
    -- Configuration
    config JSONB NOT NULL,
    framework VARCHAR(50),
    
    -- Status
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    -- Results
    output JSONB,
    error TEXT,
    
    -- Performance
    duration_ms INT,
    llm_calls INT DEFAULT 0,
    tokens_used INT DEFAULT 0,
    
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    CONSTRAINT valid_status CHECK (status IN (
        'pending', 'running', 'completed', 'failed', 'rolled_back'
    )),
    CONSTRAINT valid_framework CHECK (framework IN (
        'crewai', 'langgraph', 'autogen', 'custom'
    ))
);

CREATE INDEX idx_agents_execution ON agents(execution_id);
CREATE INDEX idx_agents_status ON agents(status);
```

#### **Checkpoints & Rollbacks**

```sql
-- Checkpoints (state snapshots)
CREATE TABLE checkpoints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id UUID NOT NULL REFERENCES executions(id) ON DELETE CASCADE,
    agent_id UUID REFERENCES agents(id) ON DELETE CASCADE,
    
    -- Checkpoint identity
    checkpoint_name VARCHAR(255) NOT NULL,
    checkpoint_index INT NOT NULL,
    
    -- State storage
    state_size_bytes INT NOT NULL,
    state_blob_uri VARCHAR(1000) NOT NULL,
    checksum VARCHAR(64) NOT NULL,
    
    -- Validation
    preconditions JSONB,
    postconditions JSONB,
    validation_passed BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    compression_type VARCHAR(50) DEFAULT 'gzip',
    
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP,
    
    UNIQUE(execution_id, checkpoint_name)
);

CREATE INDEX idx_checkpoints_execution ON checkpoints(execution_id);
CREATE INDEX idx_checkpoints_agent ON checkpoints(agent_id);
CREATE INDEX idx_checkpoints_created ON checkpoints(created_at);

-- Rollbacks (recovery history)
CREATE TABLE rollbacks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id UUID NOT NULL REFERENCES executions(id) ON DELETE CASCADE,
    
    from_checkpoint_id UUID REFERENCES checkpoints(id),
    to_checkpoint_id UUID NOT NULL REFERENCES checkpoints(id),
    
    -- Trigger
    triggered_by UUID REFERENCES users(id),
    trigger_reason VARCHAR(255) NOT NULL,
    trigger_type VARCHAR(50) DEFAULT 'manual',
    
    -- Status
    status VARCHAR(50) DEFAULT 'in_progress',
    started_at TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP,
    
    -- Results
    rollback_success BOOLEAN,
    error TEXT,
    
    -- Metadata
    affected_agents UUID[],
    metadata JSONB DEFAULT '{}',
    
    CONSTRAINT valid_status CHECK (status IN ('in_progress', 'completed', 'failed')),
    CONSTRAINT valid_trigger CHECK (trigger_type IN ('manual', 'automatic', 'policy'))
);

CREATE INDEX idx_rollbacks_execution ON rollbacks(execution_id);
CREATE INDEX idx_rollbacks_from_checkpoint ON rollbacks(from_checkpoint_id);
CREATE INDEX idx_rollbacks_to_checkpoint ON rollbacks(to_checkpoint_id);
CREATE INDEX idx_rollbacks_started ON rollbacks(started_at);
```

#### **Consensus & Coordination**

```sql
-- Consensus logs (Raft log)
CREATE TABLE consensus_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id UUID NOT NULL REFERENCES executions(id) ON DELETE CASCADE,
    
    -- Raft metadata
    term INT NOT NULL,
    log_index INT NOT NULL,
    
    -- Message content
    sender_agent_id UUID NOT NULL REFERENCES agents(id),
    receiver_agent_id UUID REFERENCES agents(id),
    message_type VARCHAR(50) NOT NULL,
    message JSONB NOT NULL,
    
    -- Consensus status
    consensus_reached BOOLEAN DEFAULT FALSE,
    acks_received INT DEFAULT 0,
    acks_required INT NOT NULL,
    
    -- Timing
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    committed_at TIMESTAMP,
    
    UNIQUE(execution_id, log_index),
    CONSTRAINT valid_message_type CHECK (message_type IN (
        'handoff', 'state_update', 'completion', 'failure'
    ))
);

CREATE INDEX idx_consensus_logs_execution ON consensus_logs(execution_id);
CREATE INDEX idx_consensus_logs_term ON consensus_logs(term);
CREATE INDEX idx_consensus_logs_sender ON consensus_logs(sender_agent_id);

-- Consensus acknowledgments
CREATE TABLE consensus_acks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    consensus_log_id UUID NOT NULL REFERENCES consensus_logs(id) ON DELETE CASCADE,
    agent_id UUID NOT NULL REFERENCES agents(id),
    
    ack_received_at TIMESTAMP NOT NULL DEFAULT NOW(),
    valid BOOLEAN DEFAULT TRUE,
    
    UNIQUE(consensus_log_id, agent_id)
);

CREATE INDEX idx_consensus_acks_log ON consensus_acks(consensus_log_id);
```

#### **Policies & Recovery**

```sql
-- Execution policies
CREATE TABLE execution_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    workflow_id UUID REFERENCES workflows(id) ON DELETE CASCADE,
    
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Policy definition
    policy_type VARCHAR(50) NOT NULL,
    policy_config JSONB NOT NULL,
    
    -- Version control
    version INT NOT NULL DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    CONSTRAINT valid_policy_type CHECK (policy_type IN (
        'timeout', 'retry', 'recovery', 'rollback', 'notification'
    ))
);

CREATE INDEX idx_execution_policies_tenant ON execution_policies(tenant_id);
CREATE INDEX idx_execution_policies_workflow ON execution_policies(workflow_id);
CREATE INDEX idx_execution_policies_active ON execution_policies(is_active);

-- Failures (detected issues)
CREATE TABLE failures (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id UUID NOT NULL REFERENCES executions(id) ON DELETE CASCADE,
    agent_id UUID REFERENCES agents(id),
    checkpoint_id UUID REFERENCES checkpoints(id),
    
    -- Failure classification
    failure_type VARCHAR(100) NOT NULL,
    severity VARCHAR(50) NOT NULL,
    
    -- Details
    error_message TEXT NOT NULL,
    stack_trace TEXT,
    root_cause TEXT,
    
    -- Recovery
    suggested_fix TEXT,
    recovery_action VARCHAR(100),
    recovery_status VARCHAR(50) DEFAULT 'pending',
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    detected_at TIMESTAMP NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMP,
    
    CONSTRAINT valid_severity CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    CONSTRAINT valid_failure_type CHECK (failure_type IN (
        'hallucination', 'timeout', 'tool_invocation', 
        'state_sync', 'consensus_violation', 'validation_error'
    ))
);

CREATE INDEX idx_failures_execution ON failures(execution_id);
CREATE INDEX idx_failures_type ON failures(failure_type);
CREATE INDEX idx_failures_severity ON failures(severity);
CREATE INDEX idx_failures_detected ON failures(detected_at);

-- Recovery actions
CREATE TABLE recovery_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    failure_id UUID NOT NULL REFERENCES failures(id) ON DELETE CASCADE,
    execution_id UUID NOT NULL REFERENCES executions(id) ON DELETE CASCADE,
    
    action_type VARCHAR(100) NOT NULL,
    action_config JSONB NOT NULL,
    
    -- Execution
    triggered_by UUID REFERENCES users(id),
    triggered_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    status VARCHAR(50) DEFAULT 'pending',
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    -- Results
    success BOOLEAN,
    error TEXT,
    
    metadata JSONB DEFAULT '{}',
    
    CONSTRAINT valid_action_type CHECK (action_type IN (
        'rollback', 'retry', 'prompt_edit', 'manual_intervention', 'escalate'
    )),
    CONSTRAINT valid_status CHECK (status IN (
        'pending', 'in_progress', 'completed', 'failed', 'cancelled'
    ))
);

CREATE INDEX idx_recovery_actions_failure ON recovery_actions(failure_id);
CREATE INDEX idx_recovery_actions_execution ON recovery_actions(execution_id);
CREATE INDEX idx_recovery_actions_triggered ON recovery_actions(triggered_at);
```

#### **Audit & Compliance**

```sql
-- Audit logs (all system actions)
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    -- Actor
    user_id UUID REFERENCES users(id),
    api_key_id UUID REFERENCES api_keys(id),
    
    -- Action
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    resource_id UUID,
    
    -- Changes
    old_values JSONB,
    new_values JSONB,
    
    -- Context
    ip_address INET,
    user_agent TEXT,
    request_id UUID,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    CONSTRAINT valid_resource_type CHECK (resource_type IN (
        'user', 'workflow', 'execution', 'checkpoint', 'policy', 'api_key', 'role'
    ))
);

CREATE INDEX idx_audit_logs_tenant ON audit_logs(tenant_id);
CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_logs_created ON audit_logs(created_at);

-- Partition audit logs by month
CREATE TABLE audit_logs_2025_11 PARTITION OF audit_logs
FOR VALUES FROM ('2025-11-01') TO ('2025-12-01');

CREATE TABLE audit_logs_2025_12 PARTITION OF audit_logs
FOR VALUES FROM ('2025-12-01') TO ('2026-01-01');
```

#### **Metrics & Analytics**

```sql
-- Execution metrics (aggregated)
CREATE TABLE execution_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id UUID NOT NULL REFERENCES executions(id) ON DELETE CASCADE,
    
    -- Performance
    total_duration_ms INT NOT NULL,
    checkpoint_overhead_ms INT,
    consensus_overhead_ms INT,
    
    -- Resource usage
    total_llm_calls INT DEFAULT 0,
    total_tokens INT DEFAULT 0,
    total_cost_usd DECIMAL(10, 4) DEFAULT 0.00,
    
    -- Reliability
    checkpoint_count INT DEFAULT 0,
    rollback_count INT DEFAULT 0,
    failure_count INT DEFAULT 0,
    retry_count INT DEFAULT 0,
    
    -- Timestamps
    measured_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_execution_metrics_execution ON execution_metrics(execution_id);
CREATE INDEX idx_execution_metrics_measured ON execution_metrics(measured_at);

-- Agent metrics
CREATE TABLE agent_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    execution_id UUID NOT NULL REFERENCES executions(id) ON DELETE CASCADE,
    
    -- Performance
    duration_ms INT NOT NULL,
    wait_time_ms INT,
    
    -- LLM usage
    llm_provider VARCHAR(50),
    llm_model VARCHAR(100),
    llm_calls INT DEFAULT 0,
    tokens_used INT DEFAULT 0,
    cost_usd DECIMAL(10, 4) DEFAULT 0.00,
    
    -- Tools
    tool_calls INT DEFAULT 0,
    tool_failures INT DEFAULT 0,
    
    measured_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_agent_metrics_agent ON agent_metrics(agent_id);
CREATE INDEX idx_agent_metrics_execution ON agent_metrics(execution_id);
```

---

### 1.2 MongoDB Schema (DocumentDB)

#### **Execution Traces**

```javascript
// Collection: execution_traces
db.createCollection("execution_traces");

db.execution_traces.createIndex({ "execution_id": 1 });
db.execution_traces.createIndex({ "execution_id": 1, "timestamp": -1 });
db.execution_traces.createIndex({ "tenant_id": 1, "created_at": -1 });

// Document structure
{
  _id: ObjectId,
  execution_id: "uuid",
  tenant_id: "uuid",
  workflow_id: "uuid",
  
  traces: [
    {
      trace_id: "trace_12345",
      span_id: "span_001",
      parent_span_id: null,
      
      operation: "validate_applicant",
      agent_id: "uuid",
      
      start_time: ISODate("2025-11-12T10:00:00Z"),
      end_time: ISODate("2025-11-12T10:00:02Z"),
      duration_ms: 2000,
      
      status: "success",
      
      attributes: {
        checkpoint: "kyc_validated",
        input: { /* ... */ },
        output: { /* ... */ },
        llm_calls: 1,
        tokens: 150
      },
      
      tags: ["kyc", "validation"]
    }
  ],
  
  metadata: {
    total_spans: 10,
    failed_spans: 0,
    total_duration_ms: 15000
  },
  
  created_at: ISODate("2025-11-12T10:00:00Z"),
  updated_at: ISODate("2025-11-12T10:00:15Z")
}
```

#### **Agent Configs**

```javascript
// Collection: agent_configs
db.createCollection("agent_configs");

db.agent_configs.createIndex({ "workflow_id": 1 });
db.agent_configs.createIndex({ "tenant_id": 1 });

// Document structure
{
  _id: ObjectId,
  tenant_id: "uuid",
  workflow_id: "uuid",
  
  name: "KYC Verification Agent",
  description: "Verifies customer KYC documents",
  
  framework: "crewai",
  version: "1.2.0",
  
  config: {
    role: "KYC Specialist",
    goal: "Verify customer identity documents",
    backstory: "Expert in document verification...",
    
    llm: {
      provider: "openai",
      model: "gpt-4",
      temperature: 0.2,
      max_tokens: 500
    },
    
    tools: [
      {
        name: "document_validator",
        type: "api",
        endpoint: "https://api.validator.com/v1/validate",
        config: { /* ... */ }
      }
    ],
    
    checkpoints: [
      {
        name: "document_received",
        preconditions: ["document.type != null"],
        postconditions: ["document.validated == true"]
      }
    ],
    
    recovery_policies: {
      on_failure: "rollback",
      max_retries: 3,
      timeout_ms: 30000
    }
  },
  
  created_at: ISODate("2025-11-12T10:00:00Z"),
  updated_at: ISODate("2025-11-12T10:00:00Z")
}
```

#### **Workflow Definitions**

```javascript
// Collection: workflow_definitions
db.createCollection("workflow_definitions");

db.workflow_definitions.createIndex({ "workflow_id": 1, "version": -1 });
db.workflow_definitions.createIndex({ "tenant_id": 1 });

// Document structure
{
  _id: ObjectId,
  workflow_id: "uuid",
  tenant_id: "uuid",
  
  name: "Customer Onboarding",
  version: 2,
  
  definition: {
    agents: [
      {
        id: "kyc_agent",
        name: "KYC Agent",
        framework: "crewai",
        config_ref: ObjectId("...")
      },
      {
        id: "credit_agent",
        name: "Credit Scoring Agent",
        framework: "langgraph",
        config_ref: ObjectId("...")
      }
    ],
    
    flow: [
      {
        step: 1,
        agent: "kyc_agent",
        inputs: ["customer_data"],
        outputs: ["kyc_verified", "kyc_score"],
        checkpoints: ["kyc_validated"]
      },
      {
        step: 2,
        agent: "credit_agent",
        inputs: ["kyc_verified", "kyc_score"],
        outputs: ["credit_score"],
        depends_on: [1],
        consensus_required: true
      }
    ],
    
    policies: {
      timeout_per_agent_ms: 30000,
      max_retries: 3,
      rollback_on_failure: true
    }
  },
  
  created_at: ISODate("2025-11-12T10:00:00Z"),
  published_at: ISODate("2025-11-12T10:00:00Z")
}
```

---

### 1.3 Redis Schema (Cache Structure)

```
# Keys structure

# Sessions
session:{session_id} → {user_id, tenant_id, expires_at, permissions}
TTL: 3600 seconds (1 hour)

# Execution status (real-time)
execution:{execution_id}:status → "running"
execution:{execution_id}:progress → {current_step, total_steps, percentage}
TTL: 86400 seconds (24 hours)

# Metrics cache (today's aggregations)
metrics:today:{tenant_id} → {total_executions, success_rate, avg_duration}
TTL: 3600 seconds

# Policy cache
policy:{policy_id} → {compiled policy rules}
TTL: 7200 seconds

# Rate limiting
rate_limit:{api_key}:{endpoint} → count
TTL: 60 seconds

# Leaderboards (active executions)
active_executions → ZSET (sorted by started_at)

# Pub/Sub channels
channel:execution_events → real-time execution updates
channel:failure_alerts → real-time failure notifications
```

---

## 2. API SPECIFICATIONS (REST)

### 2.1 Authentication Endpoints

#### **POST /auth/register**

Register new user

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "first_name": "John",
  "last_name": "Doe",
  "tenant_name": "Acme Corp"
}
```

**Response (201 Created):**
```json
{
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "tenant_id": "uuid"
  },
  "tenant": {
    "id": "uuid",
    "name": "Acme Corp",
    "slug": "acme-corp"
  },
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 3600
}
```

---

#### **POST /auth/login**

Login user

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response (200 OK):**
```json
{
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "tenant_id": "uuid"
  },
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 3600
}
```

---

#### **POST /auth/refresh**

Refresh access token

**Request:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 3600
}
```

---

### 2.2 Execution Endpoints

#### **POST /api/v1/executions**

Start new execution

**Headers:**
```
Authorization: Bearer {access_token}
Content-Type: application/json
```

**Request:**
```json
{
  "workflow_id": "uuid",
  "input_params": {
    "customer_data": {
      "name": "John Doe",
      "ssn": "123-45-6789",
      "dob": "1990-01-01"
    }
  },
  "trigger_type": "api",
  "metadata": {
    "request_id": "req_12345"
  }
}
```

**Response (201 Created):**
```json
{
  "execution": {
    "id": "uuid",
    "workflow_id": "uuid",
    "status": "pending",
    "created_at": "2025-11-12T10:00:00Z"
  },
  "message": "Execution started successfully"
}
```

---

#### **GET /api/v1/executions/{execution_id}**

Get execution details

**Response (200 OK):**
```json
{
  "execution": {
    "id": "uuid",
    "workflow_id": "uuid",
    "status": "running",
    "started_at": "2025-11-12T10:00:00Z",
    "current_checkpoint": "step_2_validated",
    "progress": {
      "current_step": 2,
      "total_steps": 5,
      "percentage": 40
    },
    "agents": [
      {
        "id": "uuid",
        "name": "KYC Agent",
        "status": "completed",
        "duration_ms": 2000
      },
      {
        "id": "uuid",
        "name": "Credit Agent",
        "status": "running",
        "duration_ms": null
      }
    ],
    "metadata": {
      "checkpoint_count": 2,
      "retry_count": 0
    }
  }
}
```

---

#### **POST /api/v1/executions/{execution_id}/pause**

Pause execution

**Response (200 OK):**
```json
{
  "execution": {
    "id": "uuid",
    "status": "paused",
    "paused_at": "2025-11-12T10:05:00Z"
  },
  "message": "Execution paused successfully"
}
```

---

#### **POST /api/v1/executions/{execution_id}/resume**

Resume execution

**Response (200 OK):**
```json
{
  "execution": {
    "id": "uuid",
    "status": "running",
    "resumed_at": "2025-11-12T10:06:00Z"
  },
  "message": "Execution resumed from checkpoint: step_2_validated"
}
```

---

#### **POST /api/v1/executions/{execution_id}/cancel**

Cancel execution

**Response (200 OK):**
```json
{
  "execution": {
    "id": "uuid",
    "status": "cancelled",
    "cancelled_at": "2025-11-12T10:07:00Z"
  },
  "message": "Execution cancelled successfully"
}
```

---

### 2.3 Checkpoint Endpoints

#### **POST /api/v1/checkpoints**

Create checkpoint (internal service call)

**Request:**
```json
{
  "execution_id": "uuid",
  "agent_id": "uuid",
  "checkpoint_name": "kyc_validated",
  "state": {
    "customer": {
      "id": "cust_123",
      "verified": true,
      "score": 95
    }
  },
  "metadata": {
    "size_bytes": 1024,
    "compression": "gzip"
  }
}
```

**Response (201 Created):**
```json
{
  "checkpoint": {
    "id": "uuid",
    "execution_id": "uuid",
    "checkpoint_name": "kyc_validated",
    "state_blob_uri": "s3://omium-checkpoints/exec_123/kyc_validated/state",
    "checksum": "sha256:abc123...",
    "created_at": "2025-11-12T10:00:02Z"
  }
}
```

---

#### **GET /api/v1/checkpoints/{checkpoint_id}**

Get checkpoint details

**Response (200 OK):**
```json
{
  "checkpoint": {
    "id": "uuid",
    "execution_id": "uuid",
    "checkpoint_name": "kyc_validated",
    "state_size_bytes": 1024,
    "state_blob_uri": "s3://...",
    "checksum": "sha256:abc123...",
    "created_at": "2025-11-12T10:00:02Z"
  }
}
```

---

#### **POST /api/v1/checkpoints/{checkpoint_id}/rollback**

Rollback to checkpoint

**Request:**
```json
{
  "reason": "Hallucination detected in offer generation",
  "trigger_type": "automatic"
}
```

**Response (200 OK):**
```json
{
  "rollback": {
    "id": "uuid",
    "execution_id": "uuid",
    "from_checkpoint_id": "uuid",
    "to_checkpoint_id": "uuid",
    "status": "completed",
    "completed_at": "2025-11-12T10:08:00Z"
  },
  "execution": {
    "id": "uuid",
    "status": "rolled_back",
    "current_checkpoint": "kyc_validated"
  },
  "message": "Rollback completed successfully"
}
```

---

### 2.4 Recovery Endpoints

#### **GET /api/v1/failures**

List failures

**Query Params:**
```
?execution_id=uuid
&severity=high
&status=pending
&limit=10
&offset=0
```

**Response (200 OK):**
```json
{
  "failures": [
    {
      "id": "uuid",
      "execution_id": "uuid",
      "failure_type": "hallucination",
      "severity": "high",
      "error_message": "Generated APR = 0%, expected 2.5%-8.5%",
      "suggested_fix": "Add APR constraint to prompt",
      "detected_at": "2025-11-12T10:05:00Z"
    }
  ],
  "pagination": {
    "total": 1,
    "limit": 10,
    "offset": 0
  }
}
```

---

#### **POST /api/v1/failures/{failure_id}/recover**

Trigger recovery action

**Request:**
```json
{
  "action_type": "prompt_edit",
  "action_config": {
    "agent_id": "uuid",
    "new_prompt": "Generate offer terms. APR must be 2.5%-8.5%..."
  }
}
```

**Response (200 OK):**
```json
{
  "recovery_action": {
    "id": "uuid",
    "failure_id": "uuid",
    "action_type": "prompt_edit",
    "status": "completed",
    "success": true
  },
  "message": "Recovery action applied, execution retrying from checkpoint"
}
```

---

### 2.5 Analytics Endpoints

#### **GET /api/v1/analytics/executions**

Get execution analytics

**Query Params:**
```
?start_date=2025-11-01
&end_date=2025-11-12
&group_by=day
```

**Response (200 OK):**
```json
{
  "analytics": {
    "total_executions": 1247,
    "successful": 1201,
    "failed": 46,
    "success_rate": 0.963,
    "avg_duration_ms": 15000,
    "total_cost_usd": 124.50,
    
    "by_day": [
      {
        "date": "2025-11-01",
        "total": 120,
        "successful": 115,
        "failed": 5,
        "success_rate": 0.958
      }
    ],
    
    "failure_breakdown": {
      "hallucination": 23,
      "timeout": 15,
      "tool_invocation": 5,
      "state_sync": 3
    }
  }
}
```

---

## 3. gRPC SERVICE DEFINITIONS

### 3.1 Checkpoint Service

```protobuf
// checkpoint.proto
syntax = "proto3";

package omium.checkpoint;

import "google/protobuf/timestamp.proto";

service CheckpointService {
  rpc CreateCheckpoint(CreateCheckpointRequest) returns (CreateCheckpointResponse);
  rpc GetCheckpoint(GetCheckpointRequest) returns (GetCheckpointResponse);
  rpc ListCheckpoints(ListCheckpointsRequest) returns (ListCheckpointsResponse);
  rpc RollbackToCheckpoint(RollbackRequest) returns (RollbackResponse);
  rpc DeleteCheckpoint(DeleteCheckpointRequest) returns (DeleteCheckpointResponse);
}

message CreateCheckpointRequest {
  string execution_id = 1;
  string agent_id = 2;
  string checkpoint_name = 3;
  bytes state = 4;
  map<string, string> metadata = 5;
  
  Conditions preconditions = 6;
  Conditions postconditions = 7;
}

message Conditions {
  repeated string conditions = 1;
}

message CreateCheckpointResponse {
  string checkpoint_id = 1;
  int64 size_bytes = 2;
  string checksum = 3;
  string state_blob_uri = 4;
  google.protobuf.Timestamp created_at = 5;
}

message GetCheckpointRequest {
  string checkpoint_id = 1;
}

message GetCheckpointResponse {
  Checkpoint checkpoint = 1;
}

message Checkpoint {
  string id = 1;
  string execution_id = 2;
  string agent_id = 3;
  string checkpoint_name = 4;
  int64 state_size_bytes = 5;
  string state_blob_uri = 6;
  string checksum = 7;
  google.protobuf.Timestamp created_at = 8;
  map<string, string> metadata = 9;
}

message ListCheckpointsRequest {
  string execution_id = 1;
  int32 limit = 2;
  int32 offset = 3;
}

message ListCheckpointsResponse {
  repeated Checkpoint checkpoints = 1;
  int32 total = 2;
}

message RollbackRequest {
  string execution_id = 1;
  string checkpoint_id = 2;
  string reason = 3;
  string trigger_type = 4;
}

message RollbackResponse {
  string rollback_id = 1;
  bool success = 2;
  string message = 3;
  google.protobuf.Timestamp completed_at = 4;
}

message DeleteCheckpointRequest {
  string checkpoint_id = 1;
}

message DeleteCheckpointResponse {
  bool success = 1;
}
```

---

### 3.2 Consensus Service

```protobuf
// consensus.proto
syntax = "proto3";

package omium.consensus;

import "google/protobuf/timestamp.proto";
import "google/protobuf/struct.proto";

service ConsensusService {
  rpc BroadcastMessage(BroadcastMessageRequest) returns (BroadcastMessageResponse);
  rpc AcknowledgeMessage(AcknowledgeMessageRequest) returns (AcknowledgeMessageResponse);
  rpc GetConsensusStatus(GetConsensusStatusRequest) returns (GetConsensusStatusResponse);
  rpc ElectLeader(ElectLeaderRequest) returns (ElectLeaderResponse);
}

message BroadcastMessageRequest {
  string execution_id = 1;
  string sender_agent_id = 2;
  repeated string receiver_agent_ids = 3;
  
  MessageType message_type = 4;
  google.protobuf.Struct message = 5;
  
  int32 term = 6;
}

enum MessageType {
  MESSAGE_TYPE_UNSPECIFIED = 0;
  HANDOFF = 1;
  STATE_UPDATE = 2;
  COMPLETION = 3;
  FAILURE = 4;
}

message BroadcastMessageResponse {
  string consensus_log_id = 1;
  int32 acks_required = 2;
  bool consensus_reached = 3;
  google.protobuf.Timestamp broadcast_at = 4;
}

message AcknowledgeMessageRequest {
  string consensus_log_id = 1;
  string agent_id = 2;
  bool valid = 3;
}

message AcknowledgeMessageResponse {
  bool success = 1;
  int32 total_acks = 2;
  bool consensus_reached = 3;
}

message GetConsensusStatusRequest {
  string execution_id = 1;
}

message GetConsensusStatusResponse {
  string execution_id = 1;
  int32 current_term = 2;
  string leader_agent_id = 3;
  repeated ConsensusLog logs = 4;
}

message ConsensusLog {
  string id = 1;
  int32 term = 2;
  int32 log_index = 3;
  string sender_agent_id = 4;
  MessageType message_type = 5;
  bool consensus_reached = 6;
  int32 acks_received = 7;
  google.protobuf.Timestamp created_at = 8;
}

message ElectLeaderRequest {
  string execution_id = 1;
  string candidate_agent_id = 2;
  int32 term = 3;
}

message ElectLeaderResponse {
  bool elected = 1;
  string leader_agent_id = 2;
  int32 term = 3;
}
```

---

### 3.3 Execution Service

```protobuf
// execution.proto
syntax = "proto3";

package omium.execution;

import "google/protobuf/timestamp.proto";
import "google/protobuf/struct.proto";

service ExecutionService {
  rpc StartExecution(StartExecutionRequest) returns (StartExecutionResponse);
  rpc GetExecutionStatus(GetExecutionStatusRequest) returns (GetExecutionStatusResponse);
  rpc PauseExecution(PauseExecutionRequest) returns (PauseExecutionResponse);
  rpc ResumeExecution(ResumeExecutionRequest) returns (ResumeExecutionResponse);
  rpc CancelExecution(CancelExecutionRequest) returns (CancelExecutionResponse);
  rpc StreamExecutionEvents(StreamExecutionEventsRequest) returns (stream ExecutionEvent);
}

message StartExecutionRequest {
  string workflow_id = 1;
  google.protobuf.Struct input_params = 2;
  string trigger_type = 3;
  map<string, string> metadata = 4;
}

message StartExecutionResponse {
  string execution_id = 1;
  ExecutionStatus status = 2;
  google.protobuf.Timestamp created_at = 3;
}

enum ExecutionStatus {
  EXECUTION_STATUS_UNSPECIFIED = 0;
  PENDING = 1;
  RUNNING = 2;
  PAUSED = 3;
  COMPLETED = 4;
  FAILED = 5;
  ROLLED_BACK = 6;
  CANCELLED = 7;
}

message GetExecutionStatusRequest {
  string execution_id = 1;
}

message GetExecutionStatusResponse {
  Execution execution = 1;
}

message Execution {
  string id = 1;
  string workflow_id = 2;
  ExecutionStatus status = 3;
  google.protobuf.Timestamp started_at = 4;
  google.protobuf.Timestamp completed_at = 5;
  
  string current_checkpoint = 6;
  Progress progress = 7;
  
  repeated Agent agents = 8;
  
  google.protobuf.Struct result = 9;
  string error = 10;
}

message Progress {
  int32 current_step = 1;
  int32 total_steps = 2;
  float percentage = 3;
}

message Agent {
  string id = 1;
  string name = 2;
  string agent_type = 3;
  ExecutionStatus status = 4;
  int32 duration_ms = 5;
}

message PauseExecutionRequest {
  string execution_id = 1;
}

message PauseExecutionResponse {
  bool success = 1;
  google.protobuf.Timestamp paused_at = 2;
}

message ResumeExecutionRequest {
  string execution_id = 1;
  string from_checkpoint = 2;
}

message ResumeExecutionResponse {
  bool success = 1;
  google.protobuf.Timestamp resumed_at = 2;
}

message CancelExecutionRequest {
  string execution_id = 1;
  string reason = 2;
}

message CancelExecutionResponse {
  bool success = 1;
  google.protobuf.Timestamp cancelled_at = 2;
}

message StreamExecutionEventsRequest {
  string execution_id = 1;
}

message ExecutionEvent {
  string event_type = 1;
  google.protobuf.Timestamp timestamp = 2;
  google.protobuf.Struct data = 3;
}
```

---

## 4. DATA MODELS & TYPES (TypeScript/Python)

### 4.1 TypeScript Models (Frontend)

```typescript
// types/execution.ts

export enum ExecutionStatus {
  PENDING = 'pending',
  RUNNING = 'running',
  PAUSED = 'paused',
  COMPLETED = 'completed',
  FAILED = 'failed',
  ROLLED_BACK = 'rolled_back',
  CANCELLED = 'cancelled'
}

export interface Execution {
  id: string;
  workflow_id: string;
  tenant_id: string;
  status: ExecutionStatus;
  started_at: string;
  completed_at?: string;
  current_checkpoint?: string;
  progress: Progress;
  agents: Agent[];
  result?: Record<string, any>;
  error?: string;
  metadata: Record<string, any>;
}

export interface Progress {
  current_step: number;
  total_steps: number;
  percentage: number;
}

export interface Agent {
  id: string;
  name: string;
  agent_type: string;
  status: ExecutionStatus;
  duration_ms?: number;
  output?: Record<string, any>;
  error?: string;
}

export interface Checkpoint {
  id: string;
  execution_id: string;
  checkpoint_name: string;
  state_size_bytes: number;
  created_at: string;
  metadata: Record<string, any>;
}

export interface Failure {
  id: string;
  execution_id: string;
  failure_type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  error_message: string;
  suggested_fix?: string;
  recovery_status: string;
  detected_at: string;
}

export interface RecoveryAction {
  id: string;
  failure_id: string;
  action_type: string;
  action_config: Record<string, any>;
  status: string;
  success?: boolean;
  triggered_at: string;
  completed_at?: string;
}
```

---

### 4.2 Python Models (Backend)

```python
# models/execution.py

from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from uuid import UUID

class ExecutionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    CANCELLED = "cancelled"

class Progress(BaseModel):
    current_step: int
    total_steps: int
    percentage: float

class Agent(BaseModel):
    id: UUID
    name: str
    agent_type: str
    status: ExecutionStatus
    duration_ms: Optional[int] = None
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class Execution(BaseModel):
    id: UUID
    workflow_id: UUID
    tenant_id: UUID
    status: ExecutionStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    current_checkpoint: Optional[str] = None
    progress: Progress
    agents: List[Agent]
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class Checkpoint(BaseModel):
    id: UUID
    execution_id: UUID
    checkpoint_name: str
    state_size_bytes: int
    state_blob_uri: str
    checksum: str
    created_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)

class Failure(BaseModel):
    id: UUID
    execution_id: UUID
    failure_type: str
    severity: str
    error_message: str
    suggested_fix: Optional[str] = None
    recovery_status: str
    detected_at: datetime

class RecoveryAction(BaseModel):
    id: UUID
    failure_id: UUID
    action_type: str
    action_config: Dict[str, Any]
    status: str
    success: Optional[bool] = None
    triggered_at: datetime
    completed_at: Optional[datetime] = None
```

---

## 5. ERROR HANDLING & RESPONSE CODES

### 5.1 HTTP Status Codes

```
200 OK              - Request successful
201 Created         - Resource created successfully
204 No Content      - Successful deletion
400 Bad Request     - Invalid request body
401 Unauthorized    - Missing or invalid authentication
403 Forbidden       - Insufficient permissions
404 Not Found       - Resource not found
409 Conflict        - Resource conflict (duplicate)
422 Unprocessable   - Validation error
429 Too Many Requests - Rate limit exceeded
500 Internal Error  - Server error
503 Service Unavailable - Service down
```

### 5.2 Error Response Format

```json
{
  "error": {
    "code": "CHECKPOINT_NOT_FOUND",
    "message": "Checkpoint with ID 'abc-123' not found",
    "details": {
      "execution_id": "exec_456",
      "checkpoint_id": "abc-123"
    },
    "request_id": "req_12345"
  }
}
```

### 5.3 Error Codes

```
// Authentication
AUTH_INVALID_CREDENTIALS
AUTH_TOKEN_EXPIRED
AUTH_INSUFFICIENT_PERMISSIONS

// Execution
EXECUTION_NOT_FOUND
EXECUTION_ALREADY_RUNNING
EXECUTION_CANNOT_PAUSE
WORKFLOW_NOT_FOUND

// Checkpoint
CHECKPOINT_NOT_FOUND
CHECKPOINT_CREATION_FAILED
CHECKPOINT_CORRUPTED
ROLLBACK_FAILED

// Consensus
CONSENSUS_NOT_REACHED
LEADER_ELECTION_FAILED
MESSAGE_BROADCAST_FAILED

// Rate Limiting
RATE_LIMIT_EXCEEDED
QUOTA_EXCEEDED

// Validation
INVALID_INPUT
MISSING_REQUIRED_FIELD
INVALID_FIELD_FORMAT
```

---

## 6. AUTHENTICATION & AUTHORIZATION FLOW

### 6.1 JWT Token Structure

```json
{
  "header": {
    "alg": "RS256",
    "typ": "JWT"
  },
  "payload": {
    "sub": "user_id",
    "tenant_id": "tenant_id",
    "email": "user@example.com",
    "roles": ["admin", "developer"],
    "permissions": [
      "execution:create",
      "execution:read",
      "checkpoint:rollback"
    ],
    "iat": 1699800000,
    "exp": 1699803600
  },
  "signature": "..."
}
```

### 6.2 Authorization Flow

```
Request → API Gateway
  ↓
Extract JWT from Authorization header
  ↓
Validate JWT signature (RS256)
  ↓
Check expiration
  ↓
Extract user_id, tenant_id, permissions
  ↓
Check permission against endpoint requirements
  ↓
If authorized: Forward to service
If not: Return 403 Forbidden
```

---

## 7. SERVICE INTERACTIONS (DETAILED)

### 7.1 Execution Flow

```
API Gateway receives: POST /api/v1/executions
  ↓
Auth Service validates JWT
  ↓
Workflow Manager receives request
  ├─ Load workflow definition from MongoDB
  ├─ Validate input parameters
  └─ Create execution record in PostgreSQL
  ↓
Execution Engine starts execution
  ├─ Load first agent config
  ├─ Initialize agent runtime
  └─ Send to Kafka: execution_started event
  ↓
Agent executes
  ├─ Pre-execution checkpoint (Checkpoint Manager)
  ├─ Execute LLM call
  ├─ Post-execution validation
  └─ If valid: Checkpoint saved
  ↓
Consensus Coordinator verifies agent handoff
  ├─ Broadcast message to next agent
  ├─ Wait for acknowledgment
  └─ If consensus reached: Continue
  ↓
Next agent executes...
  ↓
Execution completes
  ├─ Update execution status in PostgreSQL
  ├─ Send to Kafka: execution_completed event
  └─ Tracing Service logs complete trace to Elasticsearch
```

---

## 8. CODE EXAMPLES (IMPLEMENTATION)

### 8.1 Checkpoint Manager (Go)

```go
// checkpoint-manager/internal/handler/checkpoint.go

package handler

import (
    "context"
    "crypto/sha256"
    "encoding/hex"
    "fmt"
    
    pb "omium/proto/checkpoint"
    "omium/internal/storage"
)

type CheckpointHandler struct {
    storage storage.Storage
    pb.UnimplementedCheckpointServiceServer
}

func NewCheckpointHandler(s storage.Storage) *CheckpointHandler {
    return &CheckpointHandler{storage: s}
}

func (h *CheckpointHandler) CreateCheckpoint(
    ctx context.Context,
    req *pb.CreateCheckpointRequest,
) (*pb.CreateCheckpointResponse, error) {
    // Validate request
    if req.ExecutionId == "" {
        return nil, fmt.Errorf("execution_id is required")
    }
    
    // Calculate checksum
    checksum := sha256.Sum256(req.State)
    checksumStr := hex.EncodeToString(checksum[:])
    
    // Save to storage
    checkpoint, err := h.storage.SaveCheckpoint(ctx, &storage.Checkpoint{
        ExecutionID:    req.ExecutionId,
        AgentID:        req.AgentId,
        CheckpointName: req.CheckpointName,
        State:          req.State,
        Checksum:       checksumStr,
        Metadata:       req.Metadata,
    })
    if err != nil {
        return nil, fmt.Errorf("failed to save checkpoint: %w", err)
    }
    
    return &pb.CreateCheckpointResponse{
        CheckpointId:  checkpoint.ID,
        SizeBytes:     int64(len(req.State)),
        Checksum:      checksumStr,
        StateBlobUri:  checkpoint.StateBlobURI,
        CreatedAt:     timestamppb.Now(),
    }, nil
}

func (h *CheckpointHandler) RollbackToCheckpoint(
    ctx context.Context,
    req *pb.RollbackRequest,
) (*pb.RollbackResponse, error) {
    // Get checkpoint
    checkpoint, err := h.storage.GetCheckpoint(ctx, req.CheckpointId)
    if err != nil {
        return nil, fmt.Errorf("checkpoint not found: %w", err)
    }
    
    // Perform rollback
    rollback, err := h.storage.CreateRollback(ctx, &storage.Rollback{
        ExecutionID:  req.ExecutionId,
        ToCheckpointID: req.CheckpointId,
        Reason:       req.Reason,
        TriggerType:  req.TriggerType,
    })
    if err != nil {
        return nil, fmt.Errorf("rollback failed: %w", err)
    }
    
    // Restore state (load from S3, apply to execution)
    err = h.storage.RestoreState(ctx, req.ExecutionId, checkpoint.StateBlobURI)
    if err != nil {
        return nil, fmt.Errorf("state restoration failed: %w", err)
    }
    
    return &pb.RollbackResponse{
        RollbackId:  rollback.ID,
        Success:     true,
        Message:     "Rollback completed successfully",
        CompletedAt: timestamppb.Now(),
    }, nil
}
```

---

### 8.2 Execution Engine (Python)

```python
# execution-engine/app/main.py

from fastapi import FastAPI, HTTPException, Depends
from typing import Dict, Any
import asyncio
from uuid import UUID

from app.models import ExecutionStatus, Execution, Agent
from app.services.checkpoint import CheckpointService
from app.services.consensus import ConsensusService
from app.services.agent_runtime import AgentRuntime

app = FastAPI(title="Omium Execution Engine")

@app.post("/api/v1/executions/{execution_id}/execute")
async def execute_workflow(
    execution_id: UUID,
    checkpoint_service: CheckpointService = Depends(),
    consensus_service: ConsensusService = Depends(),
):
    """Execute workflow with checkpointing and consensus"""
    
    try:
        # Load execution from database
        execution = await get_execution(execution_id)
        
        # Update status
        execution.status = ExecutionStatus.RUNNING
        await save_execution(execution)
        
        # Load workflow definition
        workflow = await get_workflow(execution.workflow_id)
        
        # Execute agents in sequence
        for agent_config in workflow.agents:
            # Pre-execution checkpoint
            checkpoint = await checkpoint_service.create_checkpoint(
                execution_id=execution_id,
                agent_id=agent_config.id,
                checkpoint_name=f"{agent_config.name}_start",
                state=execution.current_state
            )
            
            # Initialize agent runtime
            agent = AgentRuntime(
                config=agent_config,
                execution_id=execution_id
            )
            
            # Execute agent
            try:
                result = await agent.execute(execution.input_params)
                
                # Validate post-conditions
                if not await validate_postconditions(result, agent_config):
                    raise ValueError("Post-condition validation failed")
                
                # Post-execution checkpoint
                await checkpoint_service.create_checkpoint(
                    execution_id=execution_id,
                    agent_id=agent_config.id,
                    checkpoint_name=f"{agent_config.name}_complete",
                    state=result
                )
                
                # Update execution state
                execution.current_state = result
                
                # Broadcast to next agent (consensus)
                if agent_config.next_agent:
                    await consensus_service.broadcast_message(
                        execution_id=execution_id,
                        sender_agent_id=agent_config.id,
                        receiver_agent_id=agent_config.next_agent,
                        message=result
                    )
                
            except Exception as e:
                # Failure detected
                await handle_failure(
                    execution_id=execution_id,
                    agent_id=agent_config.id,
                    error=str(e),
                    checkpoint_id=checkpoint.id
                )
                raise
        
        # Execution completed
        execution.status = ExecutionStatus.COMPLETED
        execution.result = execution.current_state
        await save_execution(execution)
        
        return {"execution_id": execution_id, "status": "completed"}
        
    except Exception as e:
        # Update status to failed
        execution.status = ExecutionStatus.FAILED
        execution.error = str(e)
        await save_execution(execution)
        
        raise HTTPException(status_code=500, detail=str(e))

async def handle_failure(
    execution_id: UUID,
    agent_id: UUID,
    error: str,
    checkpoint_id: UUID
):
    """Handle agent failure with recovery"""
    
    # Log failure
    failure = await create_failure(
        execution_id=execution_id,
        agent_id=agent_id,
        error=error
    )
    
    # Trigger recovery orchestrator
    await trigger_recovery(failure.id, checkpoint_id)
```

---

This LLD document is **production-ready**. Every API endpoint, database table, gRPC service, and code example is designed for immediate implementation.

**Document End**

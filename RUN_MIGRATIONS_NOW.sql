-- Run this SQL directly on your database
-- Copy and paste this entire file into your database client (pgAdmin, DBeaver, etc.)
-- Or use: psql -h omium-postgres-production.ck5amem0uk6r.us-east-1.rds.amazonaws.com -U omium_admin -d omium_production -f RUN_MIGRATIONS_NOW.sql

-- Execution Engine Schema Migration
CREATE TABLE IF NOT EXISTS executions (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,
    workflow_id VARCHAR(255) NOT NULL,
    agent_id VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    input_data JSONB DEFAULT '{}'::jsonb,
    output_data JSONB,
    error_message TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    CONSTRAINT valid_status CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled'))
);

CREATE INDEX IF NOT EXISTS idx_executions_tenant_id ON executions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_executions_workflow_id ON executions(workflow_id);
CREATE INDEX IF NOT EXISTS idx_executions_status ON executions(status);
CREATE INDEX IF NOT EXISTS idx_executions_tenant_status ON executions(tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_executions_created_at ON executions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_executions_tenant_created ON executions(tenant_id, created_at DESC);

CREATE TABLE IF NOT EXISTS workflows (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,
    created_by VARCHAR(255),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    workflow_type VARCHAR(50) NOT NULL,
    definition JSONB NOT NULL,
    version INT NOT NULL DEFAULT 1,
    config JSONB DEFAULT '{}'::jsonb,
    status VARCHAR(50) DEFAULT 'draft',
    published_at TIMESTAMP,
    tags TEXT[] DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMP,
    CONSTRAINT valid_workflow_status CHECK (status IN ('draft', 'published', 'archived')),
    CONSTRAINT valid_workflow_type CHECK (workflow_type IN ('crewai', 'langgraph', 'autogen', 'semantic_kernel', 'custom'))
);

CREATE INDEX IF NOT EXISTS idx_workflows_tenant_id ON workflows(tenant_id);
CREATE INDEX IF NOT EXISTS idx_workflows_status ON workflows(status);
CREATE INDEX IF NOT EXISTS idx_workflows_type ON workflows(workflow_type);
CREATE INDEX IF NOT EXISTS idx_workflows_tenant_status ON workflows(tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_workflows_tags ON workflows USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_workflows_created_at ON workflows(created_at DESC);

CREATE TABLE IF NOT EXISTS workflow_versions (
    id VARCHAR(36) PRIMARY KEY,
    workflow_id VARCHAR(36) NOT NULL,
    tenant_id VARCHAR(255) NOT NULL,
    version INT NOT NULL,
    definition JSONB NOT NULL,
    config JSONB DEFAULT '{}'::jsonb,
    created_by VARCHAR(255),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(workflow_id, version)
);

CREATE INDEX IF NOT EXISTS idx_workflow_versions_workflow_id ON workflow_versions(workflow_id);
CREATE INDEX IF NOT EXISTS idx_workflow_versions_tenant_id ON workflow_versions(tenant_id);


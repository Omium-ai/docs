## Omium User Flow & Integration Design (Draft)

This document captures how a developer uses Omium as an **operating system for fault‑tolerant multi‑agent AI systems**, and what we need to support that end‑to‑end flow. No implementation details here – just product and system behaviour.

---

## 1. Product mental model

- **What Omium is**
  - **Reliability + safety + observability layer** that sits around/under existing AI agent frameworks (CrewAI, LangGraph, Sematic, etc.).
  - Think of it as the **control plane** and **safety net**: retries, timeouts, circuit‑breaking, checkpointing, failure analysis, and usage tracking.

- **What Omium is *not***
  - Not yet another agent framework where you must re‑author everything.
  - Instead, you can:
    - Keep defining agents/workflows in CrewAI/LangGraph/etc.
    - Use **Omium SDK/CLI** and **Omium workflows** to route execution *through* Omium for reliability and billing.

- **Core objects in Omium**
  - **Tenant / Account** – maps to customer / team.
  - **API keys** – bound to a tenant; optionally to environment (dev/prod) and budget/quota.
  - **Credits / Tokens** – monetary abstraction; decremented as users run workflows.
  - **Workflows (Automation)** – Omium’s view of a workflow (can wrap an external framework’s workflow).
  - **Executions** – concrete runs of workflows, with checkpoints, failures, and analytics.

---

## 2. End‑to‑end user flow (happy path)

### 2.1. From marketing to app

1. **User lands on `omium.ai`** (marketing site).
2. Clicks **“Get started” / “Sign up”**.
3. Redirected to auth (our auth‑service) and completes sign up / login.
4. On success, redirected to **`app.omium.ai` → Overview page** (current Overview in the app).

### 2.2. First‑time experience in the app

On the **Overview** page, we should orient the user around a clear “first 5 minutes”:

- Show a **3–step “Get started” checklist**:
  1. **Add credits** (Billing).
  2. **Create an API key** (API section).
  3. **Install SDK & run your first workflow** (Docs + CLI).

- Overview also surfaces:
  - Current **credit balance** and **usage** at a glance.
  - Links to:
    - **Documentation** (full SDK/CLI and framework integration guides).
    - **Automation** page.
    - **Failures** and **Analytics** pages (once they have data).

### 2.3. Billing & pricing (credits model)

High‑level behaviour we need:

- **Billing page**
  - Shows:
    - Current **balance in USD** and **credits**.
    - Simple **history** of top‑ups and large usage debits.
  - Actions:
    - **Top up** with:
      - Minimum: **$10**.
      - Common presets: **$20, $50, $100…**
    - Potential **plans** (e.g. $39/mo etc.) – but the core is **pay‑as‑you‑go**.

- **Credits / tokens**
  - When the user pays $X, we convert to **credits** (e.g. 1$ → N credits – to be decided).
  - Credits are **attached at tenant level**, but:
    - We may show **per‑API‑key limits** / soft caps for safety.

- **Enforcement model (conceptual)**
  - Every request that uses an API key hits:
    - **Auth + API‑key service** → validates key, tenant, and status.
    - **Billing/usage service** → checks if enough credits remain (or if key is allowed to go negative inside a plan).
  - On insufficient credits:
    - Return a clear error (e.g. `402 Payment Required` / custom `CREDITS_EXHAUSTED` code).
    - Frontend and SDK surface: “You’ve exhausted your Omium credits; please top up.”

### 2.4. API keys & auth flow

In the app:

- **API / Keys page**
  - Shows list of keys with:
    - Name/label.
    - Created at / last used.
    - Status: active / revoked.
    - Optional **spend cap** or **environment tag** (dev/stage/prod).
  - Actions:
    - Create new key (user chooses name + maybe environment).
    - Regenerate secret (rotates, old one invalid).
    - Revoke.

In the backend:

- Each key maps to:
  - `tenant_id`
  - `api_key_id`
  - Optional: `env`, `spend_limit`, `permissions`, etc.
- The **JWT middleware** you already have:
  - Either validates a session token (for logged‑in dashboard),
  - Or validates a **signed API key token** coming from SDK/CLI.

---

## 3. SDK & CLI onboarding flow

### 3.1. Installing SDK

Developer is on their own machine:

1. From Docs or Overview, they see quickstart:
   - `pip install omium` (Python SDK).
2. They have already:
   - Logged into Omium.
   - Topped up some credits.
   - Created at least one **API key**.

### 3.2. CLI / SDK initialization

We want the first CLI experience to be smooth and opinionated:

- User runs (example):

```bash
omium init
```

- CLI flow (conceptual):
  - Ask: “Paste your Omium API key”  
    - (Optional) Ask for email/password or use a device‑code login; but **API‑key‑only** is usually cleaner and avoids storing passwords locally.
  - CLI calls Omium API:
    - Verifies the key and tenant.
    - Returns:
      - Tenant name.
      - Available credits.
      - Default environment.
  - CLI writes a **local config file**, e.g.:
    - API base URL (prod vs staging).
    - `tenant_id`.
    - `api_key_id` (and secret or token, in a safe store if possible).

- From then on:
  - SDK calls like `omium.run_workflow(...)` automatically:
    - Attach the key/token.
    - Route via Omium **execution gateway**.

### 3.3. Runtime behaviour vs credits

- Every SDK‑mediated call:
  - Is associated with a **workflow** + **execution**.
  - Is **metered** (e.g. per step, per token, per provider call – we’ll refine pricing).
  - Decrements credits.
- When credits are near zero:
  - Backend can:
    - Soft‑warn via headers / events.
    - Hard‑stop when exhausted.
  - Frontend and CLI surface this clearly.

---

## 4. Integrating external agent frameworks (CrewAI, LangGraph, Sematic)

Goal: let users **keep** using their preferred frameworks, but route **execution through Omium** for reliability, failure handling, and analytics.

### 4.1. Two levels of integration

1. **SDK‑only integration (black‑box workflows)**
   - User keeps their existing workflow code in CrewAI/LangGraph/Sematic.
   - They:
     - Install Omium SDK.
     - Wrap entrypoints / calls with Omium primitives (e.g. `omium.start_execution(...)`, `omium.checkpoint(...)`, `omium.capture_failure(...)`).
   - Pros:
     - Minimal friction.
     - No need for a full import/export format initially.
   - Omium still:
     - Tracks executions.
     - Handles retries and timeouts where allowed.
     - Surfaces failures in **Failures** page and metrics in **Analytics**.

2. **Workflow import into Omium Automation**
   - For deeper integration, user can **export** a workflow description from their framework and **import** it into Omium’s **Automation** page.
   - That imported spec becomes an **Omium Workflow** that:
     - Is editable in the **Automation** UI.
     - Is executable via **execution‑engine**.

### 4.2. CrewAI (conceptual integration)

- Today, CrewAI workflows are defined in **Python code**:
  - You define agents, tasks, tools, then assemble them into a `Crew`.
  - There is no standard JSON export in the core library.

- Our approach:
  - Define an **“Omium Workflow Spec v0”** (JSON) that captures:
    - High‑level steps (tasks).
    - Agents (roles, LLMs, tools).
    - Dependencies / ordering.
  - Provide an adapter in the Omium SDK:
    - Example: `omium.adapters.crew.export_workflow(crew: Crew) -> dict`
    - User runs:

```bash
omium export-crew path/to/workflow.py:crew_object_name > my_workflow.json
```

  - Then:
    - In **Automation** page, they click “Import from JSON”.
    - Upload `my_workflow.json`.
    - Omium creates a new Workflow record tied to that spec.

- Execution:
  - Either:
    - Omium calls out to user’s environment where CrewAI runs (webhook / gRPC model), or
    - The user runs CrewAI locally but **instruments** it with Omium SDK to report steps/checkpoints back.

### 4.3. LangGraph (conceptual integration)

- LangGraph defines workflows as **graphs of nodes** (Runnables) with edges.
- There are APIs for:
  - Saving graphs, inspecting nodes and edges programmatically.

- Our approach:
  - Similar pattern:
    - `omium.adapters.langgraph.export_graph(graph) -> Omium Workflow Spec`.
    - CLI command to export:

```bash
omium export-langgraph path/to/graph.py:graph_obj > my_workflow.json
```

  - Imported JSON is stored in Omium’s Workflow model.
  - Omium can:
    - Visualize the graph in Automation.
    - Control retries, timeouts, and checkpointing per node.

### 4.4. Sematic (or similar DAG frameworks)

- Sematic and similar tools (e.g. “semantic” frameworks) typically represent **DAGs of Python functions**.
- They often have:
  - Internal representation for DAGs.
  - Potential serialization methods.

- Our approach:
  - Same pattern:
    - Write an adapter to transform a Sematic DAG into Omium Workflow Spec.
    - Export as JSON and import via Automation UI.

### 4.5. Omium Workflow Spec (high‑level requirements)

We do **not** define the full schema here, but key fields we will need:

- Metadata:
  - `name`, `description`, `source_framework` (crewai / langgraph / sematic / custom), `version`.
- Nodes / steps:
  - ID, type (agent_task, tool_call, decision, etc.).
  - Inputs/outputs, parameters.
  - Retry policy, timeout, concurrency hints.
- Edges:
  - From node → to node.
  - Conditions (e.g. on success / on failure).
- Checkpointing:
  - Which steps produce checkpoints.
  - Payload shape (for later replay).

This spec lives in **workflow‑manager** and is consumed by **execution‑engine**.

---

## 5. How app pages support this flow

### 5.1. Overview page

- Must clearly:
  - Show **credits** and basic usage.
  - Link to:
    - Billing (top‑up).
    - API keys.
    - Documentation quickstart.
    - Automation (manage workflows).
    - Failures, Analytics (once data exists).

### 5.2. API / Keys page

- Central place for:
  - Listing & managing API keys.
  - Showing per‑key status and (optionally) spend caps.
  - Copy‑paste workflow for CLI (`omium init`).

### 5.3. Billing / Pricing

- Either:
  - Dedicated **Billing** page, or
  - Integrated into Account/Settings.
- Needs:
  - Current balance, recent transactions.
  - Simple top‑up UX (“Add $20 credits”).
  - Link to **Pricing** (marketing docs).

### 5.4. Automation page

- Represents Omium’s **workflows**:
  - List view of workflows.
  - Create / edit modal (already exists in basic form).
  - **Import JSON** action for frameworks.
  - Per‑workflow:
    - Status, last run, failures.

### 5.5. Failures page

- Central for:
  - Listing failed executions (from any framework / workflow).
  - Drilling into:
    - Checkpoints.
    - Error traces.
    - Inputs/outputs at failure point.
  - Actions:
    - Replay / rollback / ignore.

### 5.6. Analytics page

- Shows:
  - Usage over time (credits consumed, executions run).
  - Breakdown by:
    - Workflow.
    - API key.
    - Error types.

### 5.7. Documentation section

- Needs to be **complete and opinionated**:
  - Getting started:
    - Sign up, add credits, create API key.
    - Install SDK & run first Omium‑wrapped script.
  - CLI:
    - `omium init`, `omium status`, `omium export-*`.
  - Framework‑specific guides:
    - “Use Omium with CrewAI”
    - “Use Omium with LangGraph”
    - “Use Omium with Sematic / other DAG frameworks”
  - Reference:
    - API endpoints.
    - Omium Workflow Spec schema.

---

## 6. Summary of what we need to build (at a high level)

- **Account & billing layer**
  - Tenant‑level credits, top‑ups, and enforcement on each API‑key request.
- **API key management**
  - Full lifecycle in the app, with linkage to credits and usage.
- **SDK & CLI**
  - Simple `omium init` flow.
  - Automatic auth and credit‑aware execution calls.
  - Adapters for CrewAI / LangGraph / Sematic export.
- **Workflow import & Automation**
  - Define Omium Workflow Spec v0.
  - Enable JSON import into Automation.
  - Link executions to Failures & Analytics.
- **Observability**
  - Clean, actionable Failures and Analytics pages so users can trust Omium as the reliability OS.



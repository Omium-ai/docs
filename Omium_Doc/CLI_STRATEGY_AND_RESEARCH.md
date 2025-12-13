# Omium CLI & IDE Companion – Research Brief

_Last updated: November 21, 2025_

## 1. Why We’re Investing Here

- Teams building agentic systems struggle with **repeatable workflows, visibility, and controlled recovery**. Our existing backend strengths (checkpointing, rollback, telemetry) need a developer-friendly front door.
- Competing stacks are shipping opinionated CLIs and IDE agents (Salesforce Agentforce DX, AWS Nova Act, Byteable). They anchor the user journey and own the developer experience.
- Security incidents (Amazon Q Dev extension breach) show that “agentic automation” must ship with hardened defaults.

## 2. Insights from Market Research

| Source | Key Takeaways |
| ------ | ------------- |
| VS Code “Agent Mode” launch (Apr 2025) | Multi-step agent execution inside the editor; agents can plan, edit files, run terminals, hop into the browser. Highlights need for **sandboxed, observable agent actions** inside IDEs.[^1] |
| VS Code custom agents guide | Teams want to ship **role-specific agents** (e.g., reviewer, architect). Extension must let users craft opinions, policies, and tool belts.[^2] |
| AWS Nova Act IDE extension | Developers expect **natural-language tasking**, browser automation, and tight feedback loops between IDE + cloud runtime.[^3] |
| Byteable AI VS Code workspace | Offers **guided workflows, specialized agents per task, and curated prompts**; emphasizes “structured recipes” rather than raw chat.[^4] |
| Salesforce Agentforce DX pro-code tools | Provides **CLI + VS Code pairing** to manage agent lifecycle, include tests, deploy to production. Shows demand for full-stack developer workflow (init → simulate → ship).[^5] |
| TechRadar on Amazon Q exploit | Malicious agents can inject destructive commands. Security guardrails, policy enforcement, and audit trails must be first-class.[^6] |

## 3. Core Problems to Solve

1. **Orchestrating complex agent projects** – Users lack scaffolding to standardize multi-agent recipes, environment configs, and observability hooks.
2. **Trust & recovery** – Without first-class checkpoint tooling, users fear “runaway” automations. Our differentiator is baked-in rollback & replay.
3. **Multi-surface parity** – Developers want the same primitives in CI pipelines (CLI), interactive explorations (IDE), and hosted dashboards.
4. **Secure automation** – Need policy enforcement, approval workflows, and blast-radius limits for commands/tools agents may execute.

## 4. Omium CLI – Pillars & Feature Set

### 4.1 Experience Pillars
- **Declarative projects** – `omium init` scaffolds repo layout (workflows, agents, tests, environment manifests) with editable templates.
- **Observable execution** – Every `omium run` automatically streams checkpoints, events, and diffs to terminal (live view) and records them for replay.
- **Safe-by-default automation** – Policy profiles (`omium policy apply --profile staging`) gate which tools or APIs an agent can touch.
- **Lifecycle parity** – Commands compose into CI-friendly steps: `validate`, `simulate`, `deploy`, `rollback`.

### 4.2 Command Surface (v1 candidates)
| Command | Purpose |
| ------- | ------- |
| `omium init [template]` | Scaffold project with best-practice recipes (CrewAI, LangGraph, browser automation, data pipelines). |
| `omium agent add` / `omium worker add` | Generate agent skeletons with default checkpoint decorators and policy stubs. |
| `omium workflow simulate` | Local dry-run with deterministic mode (replay from stored checkpoints). |
| `omium run <workflow>` | Execute workflow against configured backend (local sandbox or Omium Cloud). Streaming logs + checkpoints inline. |
| `omium replay <execution-id>` | Time-travel replay using stored checkpoints. Optionally mutate state for testing fixes. |
| `omium diff <execution-id>` | Compare checkpoints between runs to surface behavioral drift. |
| `omium deploy` | Package + ship workflows/agents to environments (dev/stage/prod). |
| `omium policy lint` | Validate guardrail configs (allowed tools, rate limits, approval steps). |
| `omium doctor` | Diagnose connectivity, version mismatches, schema drift across environments. |

### 4.3 Integration Hooks
- **Config-driven** (`omium.yaml`) describing agents, tools, policies, deployment targets.
- **Plugin system** – enable community / customer extensions (e.g., custom evaluators, connectors) loaded via PyPI package entry points.
- **Event webhooks** – CLI emits structured events (JSON) to feed dashboards, SIEM, or chat alerts.

## 5. VS Code Extension – Companion Objectives

1. **Agent workbench** – Visual editor for workflows, with drag/drop checkpoint nodes referencing CLI definitions.
2. **Embedded Omium terminal** – Reuse CLI commands inside VS Code, but augmented with inline explanations, auto-fix suggestions.
3. **Agent sandbox** – Harness Agent Mode APIs to let an Omium “copilot” agent execute permissible actions (edit files, run tests) with our policy enforcement and checkpoint logging.[^1]
4. **Template gallery & snippets** – Provide curated recipes (incident postmortem bots, browser RPA, L3 triage) aligning with CLI templates.
5. **Secure task runner** – For every agent-issued command, show diff, policy validation status, and allow manual approval when required (mitigate risks highlighted by Amazon Q incident).[^6]

## 6. “Revolutionary” Differentiators

1. **Checkpoint-native developer tools** – Only platform where CLI automatically captures state snapshots, enabling deterministic replay, delta diffing, and quick postmortems.
2. **Policy + Guardrail DSL** – CLI/extension bundle with domain-specific language to express tool permissions, rate limits, human approvals, and data redaction. Enforced at runtime.
3. **Human-in-the-loop automation loops** – Combine CLI live runs with notifications (Slack/Teams) letting operators inject decisions mid-run (approve/deny, edit prompt, change branch).
4. **Multi-environment hygiene** – Provide “shadow mode” where workflows run in observe-only mode to generate reliability metrics before going active.
5. **First-class observability** – Tight loop with Omium dashboards: CLI attaches trace IDs, enabling hop-to dashboard, analyze, replay from same terminal.

## 7. Implementation Roadmap (High-Level)

1. **Foundations (Weeks 1–4)**  
   - Spec CLI architecture, config schema, plugin interface.  
   - Build `init`, `run`, `replay` core commands using existing Omium APIs.  
   - Instrument checkpoint streaming + local log viewer.

2. **Safety & Policy (Weeks 5–8)**  
   - Ship policy linting + enforcement hooks.  
   - Integrate approval prompts + safe execution sandbox.  
   - Add telemetry events for dashboards.

3. **IDE Companion (Weeks 9–12)**  
   - Create VS Code extension skeleton; embed CLI.  
   - Implement workflow visualizer + template browser.  
   - Integrate Agent Mode actions with Omium guardrails.

4. **Advanced Tooling (Weeks 13–16)**  
   - CLI diffing, doctor, deployment flows.  
   - Extension security audits, hardened sandbox.  
   - Publish SDK hooks for third-party integrations.

## 8. Success Metrics

- **Adoption**: % of active Omium projects initialized via CLI templates; weekly CLI MAUs.  
- **Reliability**: Reduction in mean time to fix agent incidents thanks to replay/diff features.  
- **Security**: Number of prevented policy violations; zero high-severity incidents.  
- **Community**: Volume of published plugins/templates; marketplace ratings.  
- **Developer NPS**: Survey feedback on ease-of-use vs prior workflow.

---

[^1]: “Agent Mode – Autonomous Coding in VS Code,” Microsoft, Apr 7 2025.  
[^2]: “Customizing GitHub Copilot with your own agents,” Microsoft VS Code Docs.  
[^3]: “Accelerate AI Agent Development with the Nova Act IDE Extension,” AWS Blog.  
[^4]: “Byteable AI VS Code Extension,” Byteable.ai product page.  
[^5]: “Introducing Agentforce DX Pro-Code Tools,” Salesforce Developers Blog, May 2025.  
[^6]: “Amazon’s AI Coding Agent Was Hacked to Inject Data-Wiping Commands,” TechRadar Pro, 2025.


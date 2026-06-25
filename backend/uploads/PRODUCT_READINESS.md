# Web Product Readiness

## Current Position

This project is now a runnable Next.js web MVP for an HTML-first PPT Agent:

- User input, session pages, upload parsing, HTML preview, artifact pages, and PPTX export exist.
- Lead Agent, Artifact Registry, Artifact Sub-agent, Coordination, Planner, Executor, Verify, Reporter, and Memory are present.
- Real OpenAI-compatible LLM calls exist for coordination, outline generation, planner summary, page HTML generation, and verify judge when an API key is configured.
- Prompt nodes are centrally visible and configurable at `/prompts`, backed by `config/prompts.json`.
- A minimal demo login gate is available for public deployment when enabled by environment variables.
- Docker deployment files are present.

## Implemented Agent Flow Mapping

| Flow Node | Current Implementation |
| --- | --- |
| User Input | `/workspace`, `/generate/[sessionId]` |
| Lead Agent 会话主控 | `src/lib/agent/lead-agent.ts` |
| 多作品识别 / 指代解析 / Artifact Registry | `lead-agent.ts`, `memory-store.ts` |
| Artifact Sub-agent | `src/lib/agent/artifact-subagent.ts` |
| Memory Reader / Writer | `src/lib/agent/memory/*` |
| Query Rewrite | prompt node `coordination.queryRewrite` |
| Intent Recognition | prompt node `coordination.intentRecognition` |
| Slot Extraction | prompt node `coordination.slotFilling` |
| Planner / ReAct Summary / TodoList | `planner.ts`, prompt node `planner.thoughtSummary` |
| Retrieval | upload text parser + configured remote retriever |
| Outline Generation | prompt node `executor.outlineGenerate` |
| Page Planning | deterministic layout planner |
| Image Search / Generation | placeholder asset generator only |
|逐页 HTML 生成 | prompt node `executor.htmlPageGenerate`, fail-fast on invalid output |
| HTML 校验 / 渲染 | `html-validator.ts`, iframe preview |
| Retry / Degrade / Replan | run overrides and UI actions exist |
| Reporter | `reporter.ts`, run cards |
| Preview / Export | artifact preview + PPTX export |

## What Is Still Not Production-Grade

1. Authentication is only a single demo-account gate. A real SaaS needs user tables, password reset, roles, audit logs, and per-user resource isolation.
2. Uploaded source documents still use local file storage. Public deployment should move uploads to managed object storage.
3. Uploaded files live on local disk. Production should use object storage and file size/type scanning.
4. RAG requires a configured remote endpoint or direct uploaded text. Production still needs embeddings, chunking, citations, and source-grounded generation.
5. Image search/generation is placeholder-only. Production needs licensed image search or generated image assets with moderation and attribution.
6. Execution is synchronous inside API requests. Long PPT generation should move to a job queue with progress events.
7. HTML-to-PPTX export is text/layout mapping, not pixel-perfect rendering. For high fidelity, add a screenshot or DOM-to-slide rendering pipeline.
8. Observability is thin. Add structured logs, run traces, model cost tracking, error alerts, and dashboard metrics.
9. Rate limiting is in-memory. Multiple instances need Redis or a managed rate-limit service.
10. Secrets must be rotated if they were ever shared, pasted into logs, screenshots, or committed.

## What You Need To Prepare

- A real model API key for an OpenAI-compatible chat completion endpoint.
- A deployment target that can run Docker or Node.js 20.
- A domain name and HTTPS certificate.
- A persistent volume for the current MVP, or a managed database/object-storage plan for a stronger version.
- A Supabase Auth user for the public demo account.

## Minimal Public Demo Environment

Set these variables on the server:

```env
NODE_ENV=production
LLM_PROVIDER=openai
OPENAI_API_KEY=your_server_side_key
OPENAI_BASE_URL=https://api.deepseek.com/v1
MODEL_GENERATOR=deepseek-chat
NEXT_PUBLIC_SUPABASE_URL=your_supabase_project_url
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=your_supabase_publishable_key
RAG_PROVIDER=mock
```

Run with Docker and mount data/config as persistent volumes:

```bash
docker build -t aippt-agent .
docker run -d \
  --name aippt-agent \
  -p 3000:3000 \
  --env-file .env.production \
  -v aippt-data:/app/data \
  -v aippt-config:/app/config \
  aippt-agent
```

For a real customer-facing product, replace the local volumes with database and object storage before scaling beyond a single server.

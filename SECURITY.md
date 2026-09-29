# Printora Security Threat Model

## Overview

Printora is a monorepo for operating Klipper/Moonraker 3D printers, maintaining
printer configuration and firmware workflows, managing print projects and
G-code, and exposing community features. Its primary runtime surfaces are:

- a FastAPI backend in `backend/app` with SQLite persistence and versioned SQL;
- a React/Vite browser client in `frontend/src`;
- a Go agent in `agent/` that runs near a printer and connects outbound to the API;
- local and cloud installation, update, backup, systemd, Nginx, and GitHub Actions
  workflows under `scripts/`, `packaging/`, and `.github/workflows/`.

The highest-value assets are control of a physical printer, firmware and Klipper
configuration, agent credentials, user sessions and MFA secrets, tenant-owned
projects and files, G-code integrity, audit history, backups, release signing or
deployment credentials, and availability of an active print. Community content
and public profiles matter primarily for privacy, attribution, moderation, and
abuse prevention. Prepared commercial metadata is not a live payment system.

## Threat Model, Trust Boundaries, and Assumptions

### Trust boundaries

1. Public browser or API client to FastAPI. Requests, headers, cookies/tokens,
   query strings, identifiers, uploads, archive contents, URLs, and social text
   are attacker-controlled until validated and authorized.
2. Authenticated user to another user, organization, printer, project, file, or
   moderation scope. Authentication does not imply ownership or administrative
   authorization; every object access must enforce owner/organization boundaries.
3. Cloud API to printer agent. Agent credentials authenticate a specific agent
   and printer. WebSocket, polling, heartbeat, job, result, and update messages
   cross an untrusted network and may be duplicated, delayed, replayed, reordered,
   or interrupted.
4. Agent to Moonraker/Klipper and the printer host. This boundary can cause
   physical movement, heating, file changes, service updates, firmware changes,
   or interruption of an active print. Read-only status is not equivalent to
   authorization for mutation.
5. Backend to SQLite and filesystem storage. Database rows, quarantine objects,
   G-code cache, generated artifacts, backups, and release files require atomic
   ownership checks and path confinement.
6. Operator or administrator to local/cloud deployment infrastructure. systemd,
   Nginx, sudoers, environment files, backup credentials, GitHub Actions secrets,
   and release bundles are privileged. Repository contributors are not implicitly
   production operators.
7. Printora to external services. GitHub release metadata, external library URLs,
   DNS, Cloudflare, object or backup destinations, and future payment/logistics
   providers are outside the product trust boundary and must be treated as
   unavailable or hostile at the protocol edge.
8. Public/community data to operational data. Sharing a project, profile, post,
   configuration, or file never grants printer, agent, organization, support, or
   infrastructure permission.

### Actors and inputs

- Anonymous attackers can call public endpoints, register accounts when enabled,
  submit authentication material, enumerate identifiers, send malformed traffic,
  and consume public content.
- Authenticated users control profile/community content, project metadata,
  uploads, external references, printer names and URLs allowed by their role, and
  commands exposed by authorized workflows.
- Compromised or counterfeit agents control heartbeat, capability, snapshot,
  result, error, update report, G-code cache, and WebSocket message payloads for
  credentials they possess.
- Moderators, support users, organization owners, and production operators have
  elevated but distinct privileges. Their actions remain authenticated, scoped,
  confirmed where risky, and auditable.
- Developers control source, tests, lockfiles, workflows, and release inputs but
  should not receive runtime secrets through the repository.

### Required invariants

- A user or agent can read or mutate only objects in its authorized owner,
  organization, printer, and role scope; identifiers alone never confer access.
- Public/community responses never expose tokens, internal paths, private printer
  addresses, agent details, support-only data, or private/quarantined files.
- A mutating or physical job has an authenticated origin, bounded validated
  payload, explicit target, correlation/idempotency identity, safe state gate,
  audit record, and a defined failure/rollback outcome.
- Replayed requests, WebSocket messages, webhooks, jobs, or update results do not
  create a second effective mutation.
- Untrusted URLs cannot reach arbitrary loopback, link-local, private, metadata,
  Unix-socket, or redirected destinations unless an explicit local-printer policy
  authorizes the exact endpoint.
- Uploads and archives remain size-limited and quarantined until type, path,
  checksum, content, ownership, and policy checks succeed. Quarantined content is
  never publicly served or executed.
- SQL uses parameters; dynamic identifiers or scripts are selected from trusted
  allowlists. SQL changes are idempotent scripts with backup and integrity checks.
- Secrets never enter source, logs, support bundles, public errors, artifacts, or
  frontend bundles. Passwords and tokens are stored as one-way digests where
  verification permits; rotation and revocation are enforceable.
- Release artifacts and dependencies are locked and verified. An unready release
  receives no public traffic, and rollback never overwrites confirmed new data.
- A lost cache, process, WebSocket, Redis instance, search index, or derived model
  cannot destroy canonical business data or bypass authorization.
- Physical safety gates fail closed. Loss of the cloud UI or agent must not stop
  Klipper from safely continuing an already active print.

### Assumptions and exclusions

- The host OS, Python/Node/Go toolchains, Moonraker, Klipper, Nginx, systemd, and
  backup provider are maintained and patched; vulnerabilities solely inside those
  upstreams are outside this repository unless Printora configures them unsafely.
- A fully compromised root account or printer host can bypass Printora controls.
  Limiting credentials, blast radius, and recovery impact remains in scope.
- Malicious printer firmware can falsify telemetry. Printora can authenticate the
  channel and retain evidence but cannot prove physical sensor truth by software
  alone.
- Social engineering, legal approval, fiscal classification, product safety
  certification, and moderation judgment are operational controls, not properties
  source code alone can guarantee.
- Local single-user mode reduces Internet exposure but does not remove threats
  from hostile files, browser content, LAN devices, plugins, or update sources.

## Attack Surface, Mitigations, and Attacker Stories

### Authentication, authorization, and tenant isolation

`backend/app/auth.py`, route dependencies, repositories, and printer/project
ownership queries protect sessions, MFA/step-up, organizations, support actions,
agents, and user data. Relevant attacks include session theft or fixation,
credential replay, weak password reset or MFA flows, IDOR across sequential IDs,
mass assignment, privilege escalation through organization roles, and support
checks based on mutable presentation fields. Controls include bounded Pydantic
schemas, token digests/prefixes, revocation fields, role checks, owner-filtered
repositories, and tests for cross-user access. Authorization must remain in the
backend even when the UI hides or disables an action.

### Printer, agent, and physical-operation boundary

`backend/app/routes/agents.py`, `backend/app/agent_pairing.py`, remote-operation
services, and `agent/internal/agent` carry jobs to printer-local Moonraker.
Realistic attacks include stolen pairing or agent credentials, a job delivered to
the wrong printer, replay or duplicate execution, forged success telemetry,
protocol downgrade, unsafe command composition, update artifact substitution, or
loss of preflight state between approval and execution. Existing controls include
short-lived pairing, revocation/rotation, protocol versions, correlation IDs,
checksums, confirmation and dry-run flows, sanitization, outbound-only agent
connectivity, reconnect/polling fallback, and persistent server job records.
Mutation handlers must remain allowlisted and revalidate live printer state.

### URLs, SSRF, and integrations

Printer URLs, external references, release APIs, storage/backup endpoints, and
future provider adapters can cross network boundaries. Attacker stories include
probing cloud metadata or localhost, DNS rebinding, redirecting from an allowed
host, injecting credentials into a URL, or causing unbounded response downloads.
`backend/app/moonraker.py` optimizes `.local` resolution and therefore requires
especially careful separation between local mode and cloud mode. Schemes, hosts,
resolved addresses, redirects, ports, timeouts, response size, and credential
forwarding must be constrained at every fetch site.

### Files, G-code, archives, and generated artifacts

Project/library uploads, G-code cache and delivery, thumbnails, reports, firmware
artifacts, and backups cross filesystem and parser boundaries. Attacks include
path traversal, symlink races, ZIP bombs, parser bombs, polyglot content, forged
extensions/content types, quota exhaustion, malicious G-code, object replacement
after validation, and cross-owner download. Existing controls include basename or
resolved-child confinement, bounded payloads, checksums, quarantine states,
preflight records, immutable snapshots, ownership metadata, and non-destructive
retention review. Validation and promotion must be atomic, and generated files
must never become executable because of user-controlled names or contents.

### Web and community surfaces

React renders API-controlled names, posts, discussions, profiles, moderation
reasons, file metadata, and errors. Stored/reflected XSS, unsafe links, CSRF on
cookie-authenticated deployments, CORS mistakes, abusive pagination/search, spam,
harassment, block bypass, private-content indexing, and moderation privilege abuse
are relevant. Current bearer-token usage and React escaping reduce some risk but
do not justify rendering raw HTML or unsafe URLs. Rate limits, output encoding,
backend visibility predicates, block rules, audit trails, and bounded pagination
must cover both direct endpoints and derived feeds/search.

### Persistence, concurrency, and recovery

SQLite scripts, repository transactions, future PostgreSQL/outbox/workers, local
storage, and backup/restore determine whether acknowledged work survives. Attacks
or failures include SQL injection, partial commits, duplicate jobs, stale leases,
lost updates, inconsistent file/row state, tampered backups, rollback to stale
data, and resource exhaustion through locks or oversized histories. Current
parameterized SQL, transaction helpers, schema checksums, pre-schema backups,
integrity checks, and bounded list limits are important. Canonical state must not
move to process memory, cache, WebSocket registries, or search indexes.

### Build, update, and deployment supply chain

GitHub Actions, lockfiles, release manifests, agent self-update, installers,
systemd/Nginx units, and sudoers can execute code with production or printer-host
privileges. Attacks include malicious dependency or action updates, compromised
workflow secrets, mutable shared environments, artifact replacement, branch
confusion, command injection through release identifiers, overbroad sudo, and an
unready deployment receiving traffic. Controls include pinned dependency locks,
SHA-256 verification, constrained release identifiers, immutable release
directories, isolated venv/frontend assets, readiness before Nginx switch,
fail-closed deploy, explicit rollback, and narrow sudo commands. GitHub Actions
should pin third-party actions by immutable commit and produce provenance/SBOM.

### Availability, observability, and privacy

Large uploads, expensive previews/search, repeated authentication, log growth,
queue saturation, agent reconnect storms, database locks, and disk exhaustion can
deny service or disrupt operations. Resource limits, timeouts, quotas, backoff with
jitter, bounded concurrency, readiness, backpressure, retention, and load tests
are required. Logs, metrics, audits, support bundles, and backups must preserve
request/job correlation without recording passwords, bearer tokens, PAN/CVV,
private G-code, full personal data, or arbitrary hostile payloads.

## Severity Calibration (Critical, High, Medium, Low)

### Critical

- Remote unauthenticated or low-privilege code execution on the cloud host,
  printer agent, or printer host.
- A route from public input to arbitrary G-code, heating, motion, firmware flash,
  destructive configuration, or unsafe update without effective authorization and
  physical-state gates.
- Compromise of production signing/deployment credentials that enables a trusted
  malicious release, or broad extraction of session/agent secrets enabling the
  same impact.
- Financial ledger or payment compromise becomes Critical only after real-money
  capabilities exist and the flaw can create or divert material value at scale.

### High

- Cross-tenant access to private projects, printer controls, G-code, organization
  administration, support data, or agent credentials.
- SSRF reaching cloud metadata, privileged localhost services, or internal
  management networks with meaningful confidentiality or control impact.
- Persistent stored XSS on an authenticated administrative/moderation surface.
- Update, upload, archive, path, or symlink flaws that overwrite privileged files
  or execute attacker-controlled artifacts.
- Duplicate or reordered jobs that can cause a second physical mutation, start the
  wrong print, or lose an acknowledged safety-critical operation.

### Medium

- Same-tenant authorization mistakes with bounded data exposure and no printer or
  administrative control.
- CSRF, CORS, redirect, rate-limit, or resource-exhaustion flaws requiring a logged
  in victim or producing recoverable service interruption without affecting an
  active print.
- Exposure of sanitized operational metadata, internal paths, software versions,
  or limited personal data that materially helps follow-on attacks.
- Backup, logging, alerting, or audit gaps that reduce recovery or detection but do
  not by themselves permit compromise.

### Low

- Minor information disclosure already visible to the same authorized user,
  low-impact enumeration, or bounded validation inconsistencies with no state
  change or meaningful privacy consequence.
- Developer-only or test-only weaknesses that require trusted local write access
  and cannot affect a produced artifact, secret, runtime configuration, or release.
- Availability issues limited to an optional local feature with a simple restart
  and no data loss, printer interruption, or cross-user impact.

Severity is lowered when the alleged attacker-controlled input is actually fixed
by a trusted operator, the affected path is unreachable in packaged/runtime
profiles, or independent backend authorization prevents the claimed outcome. It
is raised when the path crosses into physical control, secrets, tenant isolation,
privileged deployment, irreversible data loss, or broad persistent compromise.

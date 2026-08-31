# Software Requirements Specification

## Fintech Operations Dashboard

| | |
|---|---|
| **Document status** | Draft v1.0 |
| **Prepared for** | Portfolio project — engineering team reference |
| **Date** | August 31, 2026 |
| **Author** | Product & Engineering (PM/Staff Eng draft) |
| **Audience** | Engineering, Design, QA, Compliance stakeholders |

---

## Table of Contents

1. [Business Problem](#1-business-problem)
2. [User Personas](#2-user-personas)
3. [Scope](#3-scope)
4. [Functional Requirements](#4-functional-requirements)
5. [Non-Functional Requirements](#5-non-functional-requirements)
6. [User Stories](#6-user-stories)
7. [Acceptance Criteria](#7-acceptance-criteria)
8. [Database Entities](#8-database-entities)
9. [API Requirements](#9-api-requirements)
10. [Security Requirements](#10-security-requirements)
11. [Reporting Requirements](#11-reporting-requirements)
12. [Appendix](#12-appendix)

---

## 1. Business Problem

Mid-sized fintech companies (digital banks, payment processors, lending platforms) run day-to-day operations — customer support, fraud investigation, and regulatory compliance — across a patchwork of disconnected tools: a core banking/ledger admin panel, a separate fraud-scoring vendor console, a ticketing system, and spreadsheets used to track investigations and produce compliance reports. This fragmentation creates real business cost:

- **Slow customer resolution.** Support agents cannot see a unified view of a customer's identity, accounts, and transaction history, so a simple "why was my payment declined?" inquiry requires switching between three or four systems and often escalating unnecessarily.
- **Slow fraud and compliance response.** Fraud and AML (Anti-Money Laundering) analysts need to investigate suspicious activity within tight regulatory windows (e.g., SAR filing deadlines). Without a shared case record, investigations are duplicated, evidence is lost in email threads, and escalation paths are inconsistent.
- **No operational visibility.** Team leads and compliance officers lack real-time visibility into case backlog, SLA breaches, alert-to-case conversion rates, or analyst workload, making staffing and audit-readiness reactive rather than proactive.
- **Audit and regulatory risk.** Regulators (and internal/external auditors) expect a defensible, timestamped record of who looked at what customer data, why an alert was actioned a certain way, and how long an investigation took. Spreadsheet-based tracking cannot reliably produce this trail.

**The Fintech Operations Dashboard** is an internal, web-based operations tool that unifies customer search, transaction lookup, case management, alerting, and reporting into a single system of record for support, fraud, and compliance teams. The goal is to reduce case resolution time, create a defensible audit trail, and give operations leadership real-time visibility into team performance and regulatory exposure.

### 1.1 Goals

- Reduce average case handling time by giving analysts a single pane of glass for customer, account, and transaction data.
- Provide a structured, auditable case management workflow for disputes, fraud, and AML investigations.
- Surface risk signals (alerts) automatically and route them to the right queue.
- Give managers and compliance officers self-service reporting without engineering involvement.
- Establish a security and audit posture consistent with fintech regulatory expectations (PCI DSS, SOC 2, GLBA, AML/BSA program requirements) even though this is a portfolio project and not a production regulated system.

### 1.2 Non-Goals (for v1)

- This system does not move money, initiate transactions, or connect to a live payment rail. It is a read/operate layer on top of transaction and customer data (real or seeded/simulated for the portfolio build).
- This system does not replace a core banking ledger or a dedicated fraud-scoring ML engine — it consumes their outputs (transactions, risk scores) rather than computing them.
- Customer-facing functionality (self-service portals) is out of scope; this is an internal tool only.

---

## 2. User Personas

### Persona 1 — Ava Chen, Tier 1/2 Operations Analyst

- **Role:** Front-line customer support agent handling inbound tickets about declined payments, missing deposits, and account questions.
- **Goals:** Resolve customer inquiries in a single interaction; quickly confirm identity and transaction status; escalate to fraud/compliance when something looks wrong.
- **Pain points today:** Has to open the core banking admin panel and a separate transaction processor dashboard to answer one question; has no way to see if a case already exists for this customer.
- **Technical comfort:** Moderate. Uses internal tools daily but is not technical.
- **Primary modules used:** Customer Search, Transaction Lookup, Case Management (create/view only).

### Persona 2 — Marcus Webb, Fraud & AML Investigator

- **Role:** Investigates fraud alerts and suspicious-activity cases; may need to file internal escalations toward a SAR (Suspicious Activity Report) equivalent.
- **Goals:** Triage alerts quickly, build a complete evidence trail on a case, collaborate with peers, meet regulatory SLA deadlines (e.g., 30/60-day windows).
- **Pain points today:** Alerts arrive in a vendor tool with no link back to case notes; evidence lives in email; no audit trail of decisions.
- **Technical comfort:** High. Comfortable with data, filters, and structured workflows.
- **Primary modules used:** Alerts, Case Management, Transaction Lookup, Customer Search, Reports.

### Persona 3 — Priya Nair, Operations Team Lead / Compliance Manager

- **Role:** Manages a team of analysts and investigators; owns SLA performance and audit-readiness.
- **Goals:** See case backlog and SLA risk at a glance; reassign/escalate cases; produce reports for leadership and regulators without asking engineering for a one-off query.
- **Pain points today:** Has to manually compile spreadsheets from multiple exports to answer "how many open fraud cases are older than 5 days?"
- **Technical comfort:** Moderate to high; comfortable with dashboards and filters, not with SQL.
- **Primary modules used:** Reports, Case Management (oversight/reassignment), Alerts (rule tuning), all modules for spot-checks.

### Persona 4 — David Kim, Platform/Support Engineer (Internal Admin)

- **Role:** Administers the platform — user accounts, roles, alert rule configuration, integrations.
- **Goals:** Onboard/offboard users quickly and correctly, ensure least-privilege access, keep the audit log intact, respond to access/security questions from compliance.
- **Pain points today:** Access requests are handled ad hoc via Slack with no consistent record of who approved what.
- **Technical comfort:** Very high (engineer).
- **Primary modules used:** Admin/User Management, Security & Audit Log, Alerts (rule configuration).

---

## 3. Scope

### In scope (v1)

Customer Search, Transaction Lookup, Case Management, Alerts, Reports, plus the cross-cutting Authentication/Authorization, Audit Logging, and Admin/User Management needed to make those five modules usable and defensible.

### Out of scope (v1, candidates for v2+)

- Real-time payment initiation or reversal actions.
- Machine-learning-based fraud scoring (v1 consumes a `risk_score` field as input; it does not compute one).
- Customer-facing UI.
- Multi-currency/multi-region regulatory rule packs (v1 assumes a single jurisdiction, USD).
- Native mobile apps (v1 is responsive web only).

---

## 4. Functional Requirements

Each requirement has a unique ID for traceability into user stories, acceptance criteria, and test cases.

### 4.1 Customer Search (FR-CS)

| ID | Requirement |
|---|---|
| FR-CS-1 | The system shall allow an authenticated user to search for a customer by name, email, phone number, customer ID, or masked account/card identifier. |
| FR-CS-2 | Search shall support partial and fuzzy matching on name and email (e.g., "jon smith" matches "Jonathan Smith"). |
| FR-CS-3 | Search results shall display a ranked list showing name, masked contact info, customer status (active/suspended/closed), and account count, with a link to a full Customer 360 profile. |
| FR-CS-4 | The Customer 360 profile shall show identity details, linked accounts, KYC/verification status, risk tier, open/closed case history, and recent alerts for that customer. |
| FR-CS-5 | The system shall log every customer record view to the audit log, including who viewed it, when, and from which case or search context. |
| FR-CS-6 | Search results shall be paginated and support sorting by relevance, name, or last activity date. |
| FR-CS-7 | If a customer has one or more open cases, the search results and profile shall visibly flag this ("2 open cases") before any other detail. |

### 4.2 Transaction Lookup (FR-TL)

| ID | Requirement |
|---|---|
| FR-TL-1 | The system shall allow lookup of a single transaction by transaction ID, and lookup of a set of transactions by customer, account, date range, amount range, status, or channel (ACH, card, wire, internal transfer). |
| FR-TL-2 | Transaction results shall display amount, direction (debit/credit), status (pending/settled/failed/reversed), counterparty (masked where applicable), timestamp, and associated risk score if present. |
| FR-TL-3 | A transaction detail view shall show the full lifecycle/status history of that transaction (e.g., initiated → pending → settled) with timestamps. |
| FR-TL-4 | The system shall allow an analyst to attach one or more transactions directly to a case from the transaction lookup screen. |
| FR-TL-5 | The system shall allow export of a filtered transaction result set to CSV, subject to the user's role permissions and a maximum row cap (see NFR-5.4). |
| FR-TL-6 | Transaction data shall be treated as read-only within this system; no functional requirement in this document permits initiating, modifying, or reversing a transaction. |
| FR-TL-7 | The system shall visually flag transactions that are linked to an open alert or case. |

### 4.3 Case Management (FR-CM)

| ID | Requirement |
|---|---|
| FR-CM-1 | The system shall allow authorized users to create a case of type Dispute, Fraud Investigation, or AML/Compliance Review, linked to a customer and optionally to one or more transactions and/or alerts. |
| FR-CM-2 | Each case shall have a status (New, In Progress, Pending Customer/Third Party, Escalated, Closed–Resolved, Closed–No Action) and a priority (Low, Medium, High, Critical). |
| FR-CM-3 | Each case shall have an assignable owner and support reassignment, with a required reason note on reassignment. |
| FR-CM-4 | The system shall maintain a chronological activity timeline per case: notes, status changes, attachments, linked transactions/alerts, and reassignments, each timestamped and attributed to a user. |
| FR-CM-5 | The system shall support file attachments on a case (e.g., customer-submitted evidence, screenshots), with a per-file size limit and virus/malware scanning before storage. |
| FR-CM-6 | The system shall support SLA targets per case type/priority (e.g., Fraud/Critical = 2 business days to first action) and shall visually flag cases approaching or past SLA breach. |
| FR-CM-7 | The system shall prevent a case from being closed without a resolution code and a closing summary note. |
| FR-CM-8 | The system shall support internal @mention comments on a case that notify the mentioned user. |
| FR-CM-9 | The system shall support a case queue view, filterable by status, priority, type, assignee, and SLA risk, with bulk reassignment for team leads. |
| FR-CM-10 | The system shall prevent two users from editing the same case field simultaneously without warning (optimistic locking or last-write-wins with a conflict warning). |

### 4.4 Alerts (FR-AL)

| ID | Requirement |
|---|---|
| FR-AL-1 | The system shall ingest or generate alerts representing risk events (e.g., high-risk-score transaction, velocity threshold breach, sanctions/watchlist name match, login-anomaly signal) from an upstream source (real integration or simulated feed for this portfolio build). |
| FR-AL-2 | Each alert shall have a type, severity, status (New, Under Review, Escalated to Case, Dismissed), the triggering rule/reason, and links to the relevant customer/account/transaction. |
| FR-AL-3 | The system shall provide an alert queue, filterable and sortable by severity, type, age, and status, defaulting to oldest-highest-severity first. |
| FR-AL-4 | Authorized users shall be able to disposition an alert as Dismissed (with a required reason) or Escalate to Case (which creates or links to a Case Management case, carrying over context). |
| FR-AL-5 | The system shall support configurable alert rules (e.g., "transaction > $10,000 AND customer risk tier = High") manageable by Admin/Compliance roles without a code deployment. |
| FR-AL-6 | The system shall prevent duplicate alerts for the same underlying event from cluttering the queue (de-duplication window, configurable). |
| FR-AL-7 | The system shall support a "watchlist" style alert for a specific customer or account that a user is manually monitoring. |
| FR-AL-8 | Critical-severity alerts shall trigger a near-real-time notification (in-app and email) to the relevant queue/role. |

### 4.5 Reports (FR-RP)

| ID | Requirement |
|---|---|
| FR-RP-1 | The system shall provide pre-built operational reports: case volume by status/type/priority, average and p90 case resolution time, SLA breach rate, alert volume and disposition breakdown, and analyst productivity (cases closed per analyst per period). |
| FR-RP-2 | Reports shall support a configurable date range, and filters consistent with the underlying module (e.g., filter case reports by type, priority, assignee). |
| FR-RP-3 | The system shall support exporting any report to CSV and PDF. |
| FR-RP-4 | The system shall support scheduling a report to be generated and emailed on a recurring cadence (daily/weekly/monthly) to specified recipients. |
| FR-RP-5 | The system shall provide a compliance-oriented export: a full, timestamped audit trail for a given case or customer, suitable for regulator or internal-audit production. |
| FR-RP-6 | A summary dashboard (KPIs) shall be available on login, scoped to the user's role (e.g., an analyst sees "my open cases"; a team lead sees "team backlog and SLA risk"). |
| FR-RP-7 | Report access and report contents shall respect the same role-based data visibility rules as the underlying modules (see Section 10). |

### 4.6 Cross-Cutting: Authentication, Authorization & Audit (FR-SYS)

| ID | Requirement |
|---|---|
| FR-SYS-1 | The system shall require authentication (username/password plus MFA, or SSO/OIDC) for all access; there is no anonymous or public functionality. |
| FR-SYS-2 | The system shall enforce role-based access control (RBAC) with, at minimum, the roles: Analyst, Investigator, Team Lead, Compliance/Auditor (read-only, cross-team), and Admin. |
| FR-SYS-3 | The system shall write an immutable audit log entry for every read of sensitive customer/transaction data and every write action (case update, alert disposition, user role change). |
| FR-SYS-4 | Admins shall be able to create, deactivate, and change the role of user accounts, with every such change itself audit-logged. |

---

## 5. Non-Functional Requirements

| ID | Category | Requirement |
|---|---|---|
| NFR-1 | Performance | 95th-percentile API response time ≤ 400ms for search/lookup endpoints under nominal load (see NFR-3 for load definition); dashboard/report pages render initial content in ≤ 2s. |
| NFR-2 | Performance | Search-as-you-type customer search shall return results in ≤ 500ms for a database of up to 1M customer records. |
| NFR-3 | Scalability | The system shall support at least 200 concurrent internal users and a transaction table of 50M+ rows without degradation of the performance targets above, via pagination, indexing, and (if needed) read replicas. |
| NFR-4 | Availability | Target 99.5% monthly uptime for an internal tool (portfolio-scale target; production fintech ops tools typically target 99.9%+); documented planned-maintenance windows are excluded from the calculation. |
| NFR-5 | Usability/Limits | Bulk exports are capped (e.g., 50,000 rows per CSV export) with a message directing the user to narrow filters beyond that; all list views paginate rather than loading unbounded result sets. |
| NFR-6 | Accessibility | The web UI shall meet WCAG 2.1 AA for color contrast, keyboard navigation, and screen-reader labeling on all core workflows. |
| NFR-7 | Reliability/DR | Recovery Point Objective (RPO) ≤ 15 minutes and Recovery Time Objective (RTO) ≤ 4 hours for the primary datastore, via automated backups and a documented restore runbook. |
| NFR-8 | Data Integrity | All monetary values shall be stored as integer minor units (cents) with an explicit currency code; no floating-point currency arithmetic. |
| NFR-9 | Observability | The system shall emit structured logs, request-level metrics (latency, error rate, throughput), and distributed traces for all API calls, with alerting on error-rate and latency SLO breaches. |
| NFR-10 | Maintainability | Backend code shall maintain ≥ 80% automated test coverage on business logic; all API endpoints shall have contract tests; CI shall block merges on failing tests or lint errors. |
| NFR-11 | Compatibility | The web application shall support the latest two versions of Chrome, Edge, and Safari, at both desktop (≥1280px) and tablet widths. |
| NFR-12 | Auditability | Audit log entries shall be write-once (append-only) and retained for a minimum of 7 years, consistent with common fintech record-retention expectations. |
| NFR-12a | Auditability | A failed-login audit entry against an unrecognized email retains the submitted email in `log_metadata` under the same 7-year retention as every other audit entry (NFR-12), not a shorter window. **Decision, not a gap:** the email is one of the few signals available to distinguish a typo from a credential-stuffing/enumeration attempt against this account, and there is currently no API surface for reading `audit_logs` at all — it's reachable only via direct database access, not a general-access log. When an audit-log read endpoint is added, it must be scoped to compliance_auditor/admin only. Revisit the retention question itself only if a future data-minimization requirement (e.g. GDPR-style erasure) specifically demands it. |
| NFR-13 | Compliance posture | The system's data handling, access control, and logging design shall be structured to map cleanly onto PCI DSS (cardholder data), SOC 2 (security/availability), GLBA (financial privacy), and AML/BSA recordkeeping expectations, even where full certification is out of scope for a portfolio build. |
| NFR-14 | Internationalization | v1 targets a single locale (en-US) and a single currency (USD) and timezone-normalizes all timestamps to UTC in storage, displaying in the user's local timezone. |

---

## 6. User Stories

Grouped by module. Format: `US-<module>-<n>`.

### Customer Search

- **US-CS-1**: As Ava (Analyst), I want to search for a customer by phone number or email, so that I can quickly find the right account during a support call.
- **US-CS-2**: As Ava (Analyst), I want to see if a customer already has an open case before I create a new one, so that I don't duplicate work.
- **US-CS-3**: As Marcus (Investigator), I want to see a customer's risk tier and KYC status on their profile, so that I can triage how carefully to investigate their activity.

### Transaction Lookup

- **US-TL-1**: As Ava (Analyst), I want to look up a specific transaction by ID and see its full status history, so that I can tell a customer exactly why their payment is delayed.
- **US-TL-2**: As Marcus (Investigator), I want to filter a customer's transactions by amount and date range, so that I can identify a pattern of suspicious activity.
- **US-TL-3**: As Marcus (Investigator), I want to attach relevant transactions directly to a case, so that the evidence trail is complete without manual copy-pasting of transaction IDs.

### Case Management

- **US-CM-1**: As Ava (Analyst), I want to open a dispute case linked to a customer and transaction, so that the issue is tracked from a single ticket instead of scattered emails.
- **US-CM-2**: As Marcus (Investigator), I want to add timestamped notes and upload evidence to a case, so that anyone who picks it up later understands the full history.
- **US-CM-3**: As Priya (Team Lead), I want to see all cases approaching their SLA deadline across my team, so that I can reassign work before we breach a regulatory timeline.
- **US-CM-4**: As Priya (Team Lead), I want to reassign a case from one analyst to another with a required reason, so that workload stays balanced and there's a record of why the handoff happened.
- **US-CM-5**: As Marcus (Investigator), I want the system to require a resolution code and summary before I can close a case, so that closed cases are always audit-ready.

### Alerts

- **US-AL-1**: As Marcus (Investigator), I want a prioritized alert queue sorted by severity and age, so that I always work the highest-risk item first.
- **US-AL-2**: As Marcus (Investigator), I want to escalate an alert directly into a new case with context carried over, so that I don't have to re-enter customer and transaction details.
- **US-AL-3**: As David (Admin), I want to configure alert rules (thresholds, conditions) without a code deploy, so that compliance can tune detection as regulations or risk patterns change.
- **US-AL-4**: As Marcus (Investigator), I want to add a customer to a manual watchlist, so that any future activity on their account surfaces to me automatically.

### Reports

- **US-RP-1**: As Priya (Team Lead), I want a dashboard showing open case counts by priority and SLA risk, so that I can staff my team correctly each morning.
- **US-RP-2**: As Priya (Compliance Manager), I want to export a full audit trail for a specific case, so that I can respond to a regulator or internal auditor request within the required timeframe.
- **US-RP-3**: As Priya (Team Lead), I want to schedule a weekly case-volume report to be emailed to leadership automatically, so that I don't have to manually compile it every Monday.

### Admin / Security

- **US-SYS-1**: As David (Admin), I want to deactivate a departing employee's account immediately, so that access is revoked without delay.
- **US-SYS-2**: As David (Admin), I want every data access and permission change logged immutably, so that we can answer "who looked at this customer's data and when" at any time.

---

## 7. Acceptance Criteria

Acceptance criteria are written in Given/When/Then form and map to the user stories above.

### US-CS-1 — Search by phone/email

- Given I am an authenticated Analyst, when I enter a full or partial phone number or email into the search bar and submit, then I see a ranked result list of matching customers within 500ms (NFR-2), each showing name, masked contact info, status, and open-case flag.
- Given no customer matches the query, when I search, then I see a clear "no results" state with a suggestion to broaden the search.

### US-CS-2 — Existing open case visibility

- Given a customer has 1 or more open cases, when I view them in search results or their profile, then an "Open cases (N)" badge is visible before I can create a new case.
- Given I attempt to create a new case for that customer, when the case-creation form loads, then it surfaces existing open cases and asks me to confirm this is not a duplicate.

### US-TL-1 — Transaction status history

- Given a valid transaction ID, when I open its detail view, then I see every lifecycle status change with a timestamp and, where available, a reason (e.g., "failed: insufficient funds").
- Given an invalid or non-existent transaction ID, when I search for it, then I receive a clear error state, not a blank screen or stack trace.

### US-CM-1 — Create a case

- Given I am an Analyst viewing a customer or transaction, when I select "Create Case" and choose type = Dispute, then a case is created with status = New, linked to that customer (and transaction, if applicable), and I am set as the initial owner.
- Given required fields (type, customer, priority) are missing, when I submit, then the system blocks submission and highlights the missing fields.

### US-CM-3 — SLA risk visibility

- Given a case's priority defines an SLA target (FR-CM-6), when the case is within 20% of its SLA deadline, then it is flagged "At Risk" in the queue view; when the deadline has passed, it is flagged "Breached" in a visually distinct color.
- Given I am a Team Lead, when I open the case queue, then I can filter to show only At Risk and Breached cases across the whole team, not just my own.

### US-CM-5 — Closing requires resolution

- Given a case has no resolution code or closing summary, when I attempt to set status = Closed, then the system rejects the change and prompts for both fields.
- Given both fields are provided, when I close the case, then the case becomes read-only except for compliance/admin-level reopening, and a closed timestamp and closer identity are recorded.

### US-AL-2 — Escalate alert to case

- Given an open alert, when I select "Escalate to Case," then a new case is created (or I can link to an existing open case for that customer) pre-populated with the alert's customer, transaction(s), and triggering reason.
- Given the escalation completes, when I view the alert, then its status changes to "Escalated to Case" and it shows a link to the resulting case; the alert cannot be simultaneously dismissed.

### US-RP-2 — Audit trail export

- Given a case ID, when a Compliance/Auditor-role user requests an audit export, then the system generates a PDF/CSV containing every timestamped action on that case (creator, assignees, status changes, notes, attachments, linked alerts/transactions) with the identity of the actor for each entry.
- Given the export is requested, when it is generated, then the export request itself is written to the audit log.

### US-SYS-1 — Deactivate a user

- Given an Admin selects "Deactivate" on a user account, when confirmed, then that user's active sessions are invalidated within 60 seconds and subsequent login attempts are rejected.
- Given a user is deactivated, when I view the audit log, then I see who deactivated them and when.

---

## 8. Database Entities

Logical data model (relational). Field lists are representative, not exhaustive; types are illustrative (e.g., Postgres-flavored).

### 8.1 Entity summary

| Entity | Purpose |
|---|---|
| `customer` | Identity record for an end customer of the fintech product. |
| `account` | A financial account (checking, card, loan, etc.) belonging to a customer. |
| `transaction` | An individual movement of funds on an account. |
| `case` | A unit of investigative/support work: dispute, fraud investigation, or AML review. |
| `case_activity` | Append-only timeline entries for a case (notes, status changes, reassignments). |
| `case_attachment` | Files attached to a case. |
| `alert` | A system- or rule-generated risk signal. |
| `alert_rule` | A configurable rule definition that generates alerts. |
| `internal_user` | An employee/operator of this dashboard (not a customer). |
| `role` | RBAC role definition. |
| `audit_log` | Immutable record of sensitive reads and all writes. |
| `report_schedule` | A saved, recurring report configuration. |

### 8.2 Key fields and relationships

#### customer

`id (PK, uuid)`, `full_name`, `email`, `phone`, `date_of_birth (encrypted)`, `kyc_status (enum: unverified/pending/verified/rejected)`, `risk_tier (enum: low/medium/high)`, `status (enum: active/suspended/closed)`, `created_at`, `updated_at`.
→ has many `account`, has many `case` (via case.customer_id), has many `alert`.

#### account

`id (PK, uuid)`, `customer_id (FK → customer.id)`, `account_type (enum: checking/savings/card/loan)`, `masked_number`, `status`, `opened_at`, `closed_at`.
→ has many `transaction`.

#### transaction

`id (PK, uuid)`, `account_id (FK → account.id)`, `amount_cents (bigint)`, `currency (char(3))`, `direction (enum: debit/credit)`, `channel (enum: ach/card/wire/internal)`, `status (enum: initiated/pending/settled/failed/reversed)`, `counterparty_masked`, `risk_score (nullable, numeric)`, `created_at`, `settled_at (nullable)`.
→ has many `transaction_status_history` (or a JSON/event-sourced history column); referenced by `case_activity.linked_transaction_id` and `alert.transaction_id`.
*Indexes:* `(account_id, created_at)`, `(status)`, composite index supporting date-range + amount-range filters.

#### case

`id (PK, uuid)`, `case_number (human-readable, unique)`, `customer_id (FK → customer.id)`, `type (enum: dispute/fraud/aml_review)`, `status (enum: new/in_progress/pending_external/escalated/closed_resolved/closed_no_action)`, `priority (enum: low/medium/high/critical)`, `owner_id (FK → internal_user.id)`, `sla_due_at`, `resolution_code (nullable)`, `closing_summary (nullable)`, `created_at`, `closed_at (nullable)`.
→ has many `case_activity`, has many `case_attachment`; many-to-many with `transaction` and `alert` via join tables (`case_transaction_link`, `case_alert_link`).

#### case_activity

`id (PK, uuid)`, `case_id (FK)`, `actor_id (FK → internal_user.id)`, `activity_type (enum: note/status_change/reassignment/attachment_added/link_added)`, `payload (jsonb)`, `created_at`. *(Append-only; no update/delete permitted at the application layer.)*

#### case_attachment

`id (PK, uuid)`, `case_id (FK)`, `uploaded_by (FK)`, `file_name`, `storage_key`, `content_type`, `size_bytes`, `av_scan_status (enum: pending/clean/infected)`, `created_at`.

#### alert

`id (PK, uuid)`, `type (enum: high_risk_txn/velocity/sanctions_match/login_anomaly/manual_watchlist)`, `severity (enum: low/medium/high/critical)`, `status (enum: new/under_review/escalated/dismissed)`, `customer_id (FK)`, `transaction_id (nullable FK)`, `triggering_rule_id (FK → alert_rule.id, nullable for manual)`, `dismissal_reason (nullable)`, `created_at`, `resolved_at (nullable)`.

#### alert_rule

`id (PK, uuid)`, `name`, `condition_definition (jsonb — e.g., {field: amount_cents, op: gt, value: 1000000})`, `severity`, `is_active (bool)`, `created_by (FK)`, `updated_at`.

#### internal_user

`id (PK, uuid)`, `email`, `full_name`, `role_id (FK → role.id)`, `status (enum: active/deactivated)`, `mfa_enabled (bool)`, `last_login_at`, `created_at`.

#### role

`id (PK, uuid)`, `name (enum: analyst/investigator/team_lead/compliance_auditor/admin)`, `permissions (jsonb — scoped capability list)`.

#### audit_log

`id (PK, bigint, append-only)`, `actor_id (FK → internal_user.id)`, `action (enum: view/create/update/delete/export/login/permission_change)`, `resource_type`, `resource_id`, `metadata (jsonb)`, `ip_address`, `created_at`. *(Write-once; retained per NFR-12; no application-level delete/update endpoint exists for this table.)*

#### report_schedule

`id (PK, uuid)`, `report_type`, `filters (jsonb)`, `cadence (enum: daily/weekly/monthly)`, `recipients (text[])`, `created_by (FK)`, `last_run_at`, `next_run_at`.

### 8.3 Entity relationship overview (textual)

```text
customer 1---* account 1---* transaction
customer 1---* case *---* transaction   (via case_transaction_link)
customer 1---* alert *---* case         (via case_alert_link, on escalation)
case 1---* case_activity
case 1---* case_attachment
alert_rule 1---* alert
role 1---* internal_user 1---* case (as owner)
internal_user 1---* audit_log (as actor)
internal_user 1---* report_schedule (as creator)
```

---

## 9. API Requirements

RESTful JSON API, versioned under `/api/v1`. All endpoints require authentication (`Authorization: Bearer <token>`, OIDC-issued JWT) and are authorized per the RBAC matrix in Section 10.

### 9.1 Conventions

- **Pagination:** cursor-based (`?cursor=<opaque>&limit=<n>`, default `limit=25`, max `limit=200`); responses include `next_cursor`.
- **Filtering/sorting:** query params per resource (e.g., `?status=open&priority=high&sort=-created_at`).
- **Errors:** RFC 7807 `application/problem+json` — `{type, title, status, detail, instance}`.
- **Idempotency:** all `POST` endpoints that create a resource accept an `Idempotency-Key` header.
- **Rate limiting:** per-user token bucket; `429` with `Retry-After` header on breach.
- **Money:** all amounts in integer minor units plus an explicit `currency` field; never floats.
- **Timestamps:** ISO 8601 UTC.

### 9.2 Customer Search & Profile

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/customers?q=&page=` | Search customers by name/email/phone/ID. |
| GET | `/api/v1/customers/{id}` | Full Customer 360 profile. |
| GET | `/api/v1/customers/{id}/accounts` | Accounts belonging to a customer. |
| GET | `/api/v1/customers/{id}/cases` | Cases linked to a customer. |
| GET | `/api/v1/customers/{id}/alerts` | Alerts linked to a customer. |

### 9.3 Transaction Lookup

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/transactions/{id}` | Single transaction detail + status history. |
| GET | `/api/v1/transactions?account_id=&from=&to=&min_amount=&max_amount=&status=&channel=` | Filtered transaction search. |
| GET | `/api/v1/transactions/export?...filters` | CSV export (row-capped, role-gated). |

### 9.4 Case Management

| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/cases` | Create a case. |
| GET | `/api/v1/cases?status=&priority=&assignee=&sla_risk=` | List/filter case queue. |
| GET | `/api/v1/cases/{id}` | Case detail incl. timeline. |
| PATCH | `/api/v1/cases/{id}` | Update status/priority/owner (validated transitions only). |
| POST | `/api/v1/cases/{id}/notes` | Add a note. |
| POST | `/api/v1/cases/{id}/attachments` | Upload an attachment (multipart; triggers AV scan). |
| POST | `/api/v1/cases/{id}/links` | Link a transaction or alert to the case. |
| POST | `/api/v1/cases/{id}/reassign` | Reassign owner (requires `reason`). |
| POST | `/api/v1/cases/{id}/close` | Close a case (requires `resolution_code`, `closing_summary`). |

### 9.5 Alerts

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/alerts?severity=&status=&type=` | Alert queue. |
| GET | `/api/v1/alerts/{id}` | Alert detail. |
| POST | `/api/v1/alerts/{id}/dismiss` | Dismiss (requires `reason`). |
| POST | `/api/v1/alerts/{id}/escalate` | Escalate to a new or existing case. |
| GET/POST/PATCH | `/api/v1/alert-rules` | Manage alert rule definitions (Admin/Compliance only). |

### 9.6 Reports

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/reports/dashboard` | Role-scoped KPI summary for the logged-in user. |
| GET | `/api/v1/reports/cases?from=&to=&group_by=` | Case volume/SLA report data. |
| GET | `/api/v1/reports/alerts?from=&to=` | Alert volume/disposition report data. |
| GET | `/api/v1/reports/audit-trail?case_id=` | Full audit export for a case (Compliance/Admin only). |
| POST | `/api/v1/report-schedules` | Create a recurring scheduled report. |
| GET | `/api/v1/reports/{report_id}/export?format=csv\|pdf` | Export a generated report. |

### 9.7 Admin & Auth

| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/auth/login` | Credential + MFA login (or OIDC redirect flow). |
| POST | `/api/v1/auth/logout` | Invalidate current session/token. |
| GET/POST/PATCH | `/api/v1/users` | Manage internal users (Admin only). |
| GET | `/api/v1/audit-log?actor=&resource_type=&from=&to=` | Query audit log (Compliance/Admin only). |

---

## 10. Security Requirements

| ID | Requirement |
|---|---|
| SEC-1 | **Authentication.** All access requires authentication via SSO/OIDC where available, or username + password + mandatory MFA (TOTP or WebAuthn) otherwise. No shared/generic accounts. |
| SEC-2 | **Authorization (RBAC).** Every API endpoint and UI action enforces role-based permissions server-side (never client-side only). Minimum role matrix: **Analyst** — search, lookup, create/view own cases, view own alerts; **Investigator** — Analyst + escalate alerts, close cases, cross-analyst case visibility within team; **Team Lead** — Investigator + reassign any team case, view team reports; **Compliance/Auditor** — read-only across all cases/customers/audit logs, plus audit export; **Admin** — user/role management, alert rule configuration, no implicit access to customer PII beyond what's needed for support. |
| SEC-3 | **Least privilege & data minimization.** Full unmasked PII/PAN (e.g., full account number, SSN) is never returned by default; masked forms are shown, with a explicit, audit-logged "reveal" action gated to specific roles and use cases. |
| SEC-4 | **Encryption.** TLS 1.2+ for all traffic in transit. Sensitive fields (DOB, government ID numbers, if ever stored) encrypted at rest at the column level in addition to full-disk/volume encryption. |
| SEC-5 | **Audit logging.** Every view of a customer/transaction record and every write action is logged immutably (actor, action, resource, timestamp, IP) per FR-SYS-3/NFR-12, and the audit log itself has no update/delete API. |
| SEC-6 | **Session management.** Sessions expire after 30 minutes of inactivity (configurable); deactivating a user invalidates all active sessions/tokens within 60 seconds. |
| SEC-7 | **Input validation & injection defense.** All inputs validated/sanitized server-side; parameterized queries only (no dynamic SQL string concatenation); file uploads restricted by type/size and scanned for malware before persistence. |
| SEC-8 | **Rate limiting & abuse prevention.** Login endpoints apply exponential backoff/lockout after repeated failures; all APIs are rate-limited per user/IP. |
| SEC-9 | **Secrets management.** No credentials, API keys, or tokens in source control; secrets loaded from a managed secrets store (e.g., environment-injected via a vault) with rotation supported. |
| SEC-10 | **Segregation of duties.** The user who dismisses/escalates an alert or closes a case is recorded distinctly from the user who created it, supporting four-eyes review where required by policy. |
| SEC-11 | **Data retention & deletion.** Customer and case data retention follows a documented policy (e.g., 7-year minimum for financial/AML records); any deletion request is itself logged and subject to legal-hold override. |
| SEC-12 | **Third-party/vendor risk.** Any external alert-feed or KYC-vendor integration authenticates via scoped API keys/OAuth client credentials, not shared secrets, and inbound webhook payloads are signature-verified. |
| SEC-13 | **Security testing.** Dependency scanning (SCA) and static analysis (SAST) run in CI on every pull request; a penetration test or equivalent security review is expected before any production launch beyond this portfolio scope. |

---

## 11. Reporting Requirements

### 11.1 Standard reports

| Report | Description | Primary audience |
|---|---|---|
| Case Volume & Aging | Cases opened/closed over time, broken down by type/priority/status, with average and p90 age. | Team Lead |
| SLA Compliance | % of cases resolved within SLA by type/priority, list of current breaches. | Team Lead, Compliance |
| Alert Disposition | Alerts by type/severity and how they were resolved (dismissed vs. escalated), with dismissal reasons. | Compliance, Investigator |
| Analyst Productivity | Cases/alerts handled per analyst per period, average handling time. | Team Lead |
| Audit Trail Export | Full chronological, attributed action log for a case or customer. | Compliance/Auditor, external regulator response |
| Access & Permissions | Current role assignments and a history of permission changes. | Admin, Compliance |

### 11.2 Requirements

- **RPT-1**: All reports support a custom date range plus quick presets (Today, 7 days, 30 days, Quarter-to-date).
- **RPT-2**: All reports are exportable as CSV and PDF; the Audit Trail export additionally supports a structured JSON format for downstream e-discovery tooling.
- **RPT-3**: Reports can be scheduled for recurring email delivery (daily/weekly/monthly) to one or more internal recipients; scheduled report creation/edits are audit-logged.
- **RPT-4**: The role-scoped landing dashboard (FR-RP-6) refreshes at least every 5 minutes or on manual refresh, and never requires a full page reload to update filters.
- **RPT-5**: Every report respects row-level data visibility — an Analyst's report never surfaces case detail outside their team, even in aggregate drill-downs.
- **RPT-6**: Report generation for large date ranges (>90 days) runs asynchronously with a notification when ready, rather than blocking the UI.

---

## 12. Appendix

### 12.1 Glossary

- **AML** — Anti-Money Laundering.
- **BSA** — Bank Secrecy Act (US regulation underpinning AML program requirements).
- **KYC** — Know Your Customer (identity verification).
- **SAR** — Suspicious Activity Report, a regulatory filing (this system supports evidence-gathering toward one; it does not itself file with a regulator).
- **PAN** — Primary Account Number (full card/account number; must be masked per SEC-3).
- **SLA** — Service Level Agreement (here, an internal case-handling time target).
- **RPO / RTO** — Recovery Point/Time Objective, disaster-recovery targets (NFR-7).

### 12.2 Assumptions

- Data for this portfolio build is either a sanitized/synthetic dataset or a personal sandbox account; no real customer PII is used in development or demos.
- A single-tenant deployment is assumed for v1 (no multi-organization/white-label support).
- Upstream systems (core ledger, KYC vendor, fraud-scoring engine) are simulated via seed data and/or mock services rather than live third-party integrations, unless a specific integration is explicitly built out.

### 12.3 Suggested technology direction (non-binding)

A conventional, well-supported stack is recommended to keep the portfolio build focused on product/architecture quality rather than tooling risk: a typed backend (e.g., Node/TypeScript or Python) exposing the REST API in Section 9, PostgreSQL for the relational model in Section 8, a background job runner for scheduled reports and async exports, object storage for case attachments, and a React/TypeScript frontend. These are suggestions, not requirements — the functional, data, and security requirements above are the durable contract.

### 12.4 Suggested delivery milestones

1. **Foundation:** auth/RBAC, data model, audit logging skeleton.
2. **Core lookup:** Customer Search + Transaction Lookup (read-only, highest immediate value, lowest workflow complexity).
3. **Case Management:** creation, timeline, SLA tracking, closure workflow.
4. **Alerts:** queue, disposition, escalation-to-case integration.
5. **Reporting:** dashboard KPIs, standard reports, scheduled exports.
6. **Hardening:** security review pass, accessibility pass, load testing against NFR targets.

---

*End of document.*

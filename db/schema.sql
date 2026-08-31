-- ============================================================================
-- Fintech Operations Dashboard — Core Schema
-- PostgreSQL 14+
--
-- Entities: roles, users, customers, accounts, transactions, cases,
--           case_notes, alerts, reports, audit_logs, refresh_tokens
--
-- Design decisions are explained in the accompanying chat response, not
-- repeated here as comments — this file is meant to run as-is (or as the
-- body of the first Alembic revision).
-- ============================================================================

create extension if not exists pgcrypto;   -- gen_random_uuid()
create extension if not exists citext;     -- case-insensitive email
create extension if not exists pg_trgm;    -- fuzzy customer search (FR-CS-2)

create or replace function set_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;


-- ============================================================================
-- 1. roles
-- ============================================================================
create table roles (
    id          uuid primary key default gen_random_uuid(),
    name        text not null,
    description text,
    permissions jsonb not null default '{}'::jsonb,
    created_at  timestamptz not null default now(),
    updated_at  timestamptz not null default now(),
    deleted_at  timestamptz
);

create unique index ux_roles_name_active on roles (lower(name)) where deleted_at is null;

create trigger trg_roles_updated_at
before update on roles
for each row execute function set_updated_at();


-- ============================================================================
-- 2. users  (internal operators: analysts, investigators, team leads, admins)
-- ============================================================================
create table users (
    id               uuid primary key default gen_random_uuid(),
    role_id          uuid not null references roles(id) on delete restrict,
    email            citext not null,
    full_name        text not null,
    hashed_password  text not null,
    mfa_enabled      boolean not null default false,
    mfa_secret       text,   -- base32 TOTP secret; null until the user enrolls
    token_version    bigint not null default 0,   -- bumped to invalidate outstanding access tokens
    status           text not null default 'active'
                         check (status in ('active', 'deactivated')),
    last_login_at    timestamptz,
    created_at       timestamptz not null default now(),
    updated_at       timestamptz not null default now(),
    deleted_at       timestamptz
);

create unique index ux_users_email_active on users (email) where deleted_at is null;
create index ix_users_role_id on users (role_id) where deleted_at is null;

create trigger trg_users_updated_at
before update on users
for each row execute function set_updated_at();


-- ============================================================================
-- 3. customers
-- ============================================================================
create table customers (
    id                       uuid primary key default gen_random_uuid(),
    full_name                text not null,
    email                    citext,
    phone                    text,
    date_of_birth_encrypted  bytea,   -- encrypted at the application layer (KMS-backed); never plaintext
    kyc_status               text not null default 'unverified'
                                 check (kyc_status in ('unverified', 'pending', 'verified', 'rejected')),
    risk_tier                text not null default 'low'
                                 check (risk_tier in ('low', 'medium', 'high')),
    status                   text not null default 'active'
                                 check (status in ('active', 'suspended', 'closed')),
    created_at               timestamptz not null default now(),
    updated_at               timestamptz not null default now(),
    deleted_at               timestamptz
);

create unique index ux_customers_email_active on customers (email) where deleted_at is null;

create index ix_customers_email_trgm on customers using gin ((email::text) gin_trgm_ops) where deleted_at is null;
create index ix_customers_name_trgm  on customers using gin (full_name gin_trgm_ops) where deleted_at is null;
create index ix_customers_phone      on customers (phone) where deleted_at is null;
create index ix_customers_phone_trgm on customers using gin (phone gin_trgm_ops) where deleted_at is null;

-- One (column, id) composite per sortable field (app.models.customer.
-- CUSTOMER_SORTABLE_FIELDS) — the id tiebreaker is what keeps keyset
-- pagination correct, and Postgres serves both sort directions off a single
-- ascending index via a backward scan, so there's no separate desc variant.
create index ix_customers_created_at_id on customers (created_at, id) where deleted_at is null;
create index ix_customers_updated_at_id on customers (updated_at, id) where deleted_at is null;
create index ix_customers_full_name_id  on customers (full_name, id)  where deleted_at is null;
create index ix_customers_risk_tier_id  on customers (risk_tier, id)  where deleted_at is null;
create index ix_customers_status_id     on customers (status, id)     where deleted_at is null;
create index ix_customers_kyc_status_id on customers (kyc_status, id) where deleted_at is null;

create trigger trg_customers_updated_at
before update on customers
for each row execute function set_updated_at();


-- ============================================================================
-- 4. accounts
-- ============================================================================
create table accounts (
    id             uuid primary key default gen_random_uuid(),
    customer_id    uuid not null references customers(id) on delete restrict,
    account_type   text not null check (account_type in ('checking', 'savings', 'card', 'loan')),
    masked_number  text not null,   -- e.g. '**** 4471'; full PAN is never stored here
    status         text not null default 'active'
                       check (status in ('active', 'closed', 'frozen')),
    opened_at      timestamptz not null default now(),
    closed_at      timestamptz,
    created_at     timestamptz not null default now(),
    updated_at     timestamptz not null default now(),
    deleted_at     timestamptz
);

create index ix_accounts_customer_id on accounts (customer_id) where deleted_at is null;
create index ix_accounts_status      on accounts (status) where deleted_at is null;

create trigger trg_accounts_updated_at
before update on accounts
for each row execute function set_updated_at();


-- ============================================================================
-- 5. transactions  (read-only feed from the core ledger — never mutated
--                    after settlement; see NFR-8, FR-TL-6)
-- ============================================================================
create table transactions (
    id                  uuid primary key default gen_random_uuid(),
    account_id          uuid not null references accounts(id) on delete restrict,
    amount_cents        bigint not null check (amount_cents > 0),
    currency            char(3) not null default 'USD',
    direction           text not null check (direction in ('debit', 'credit')),
    channel             text not null check (channel in ('ach', 'card', 'wire', 'internal')),
    status              text not null default 'initiated'
                            check (status in ('initiated', 'pending', 'settled', 'failed', 'reversed')),
    counterparty_masked text,
    risk_score          numeric(5, 2),
    created_at          timestamptz not null default now(),
    settled_at          timestamptz,
    updated_at          timestamptz not null default now(),
    deleted_at          timestamptz
);

create index ix_transactions_account_created on transactions (account_id, created_at desc) where deleted_at is null;
create index ix_transactions_status           on transactions (status) where deleted_at is null;
create index ix_transactions_amount           on transactions (amount_cents) where deleted_at is null;
create index ix_transactions_risk_score       on transactions (risk_score) where deleted_at is null and risk_score is not null;

create trigger trg_transactions_updated_at
before update on transactions
for each row execute function set_updated_at();


-- ============================================================================
-- 6. cases
-- ============================================================================
create table cases (
    id               uuid primary key default gen_random_uuid(),
    case_number      text not null,   -- human-readable, e.g. 'CASE-2026-000482'
    customer_id      uuid not null references customers(id) on delete restrict,
    owner_id         uuid references users(id) on delete set null,
    type             text not null check (type in ('dispute', 'fraud', 'aml_review')),
    status           text not null default 'new'
                         check (status in ('new', 'in_progress', 'pending_external',
                                            'escalated', 'closed_resolved', 'closed_no_action')),
    priority         text not null default 'medium'
                         check (priority in ('low', 'medium', 'high', 'critical')),
    sla_due_at       timestamptz,
    resolution_code  text,
    closing_summary  text,
    created_at       timestamptz not null default now(),
    updated_at       timestamptz not null default now(),
    closed_at        timestamptz,
    deleted_at       timestamptz,

    constraint ck_case_closed_requires_resolution check (
        status not in ('closed_resolved', 'closed_no_action')
        or (resolution_code is not null and closing_summary is not null)
    )
);

create unique index ux_cases_case_number     on cases (case_number);
create index ix_cases_customer_id            on cases (customer_id) where deleted_at is null;
create index ix_cases_owner_id               on cases (owner_id) where deleted_at is null;
create index ix_cases_status_priority        on cases (status, priority) where deleted_at is null;
create index ix_cases_sla_due_at             on cases (sla_due_at) where deleted_at is null and status not like 'closed%';

create trigger trg_cases_updated_at
before update on cases
for each row execute function set_updated_at();

-- evidence links: a transaction can support more than one case over time,
-- so this is a real many-to-many, not a column on either side.
create table case_transaction_links (
    case_id        uuid not null references cases(id) on delete cascade,
    transaction_id uuid not null references transactions(id) on delete restrict,
    linked_by      uuid references users(id) on delete set null,
    created_at     timestamptz not null default now(),
    primary key (case_id, transaction_id)
);

create index ix_case_txn_links_transaction on case_transaction_links (transaction_id);


-- ============================================================================
-- 7. case_notes  (append-only investigative timeline entries)
-- ============================================================================
create table case_notes (
    id          uuid primary key default gen_random_uuid(),
    case_id     uuid not null references cases(id) on delete cascade,
    author_id   uuid not null references users(id) on delete restrict,
    body        text not null,
    is_system   boolean not null default false,   -- true for auto-generated notes (status/owner changes)
    created_at  timestamptz not null default now(),
    updated_at  timestamptz not null default now(),
    deleted_at  timestamptz
);

create index ix_case_notes_case_id   on case_notes (case_id, created_at) where deleted_at is null;
create index ix_case_notes_author_id on case_notes (author_id);

create trigger trg_case_notes_updated_at
before update on case_notes
for each row execute function set_updated_at();


-- ============================================================================
-- 8. alerts
-- ============================================================================
create table alerts (
    id                 uuid primary key default gen_random_uuid(),
    customer_id        uuid not null references customers(id) on delete restrict,
    transaction_id     uuid references transactions(id) on delete set null,
    case_id            uuid references cases(id) on delete set null,   -- set on escalation
    type               text not null check (type in
                           ('high_risk_txn', 'velocity', 'sanctions_match', 'login_anomaly', 'manual_watchlist')),
    severity           text not null check (severity in ('low', 'medium', 'high', 'critical')),
    status             text not null default 'new'
                           check (status in ('new', 'under_review', 'escalated', 'dismissed')),
    triggering_reason  text not null,
    dismissal_reason   text,
    created_at         timestamptz not null default now(),
    resolved_at        timestamptz,
    updated_at         timestamptz not null default now(),
    deleted_at         timestamptz,

    constraint ck_alert_dismissal_reason check (status <> 'dismissed' or dismissal_reason is not null),
    constraint ck_alert_escalation_has_case check (status <> 'escalated' or case_id is not null)
);

create index ix_alerts_customer_id    on alerts (customer_id) where deleted_at is null;
create index ix_alerts_transaction_id on alerts (transaction_id) where deleted_at is null;
create index ix_alerts_queue          on alerts (status, severity, created_at) where deleted_at is null;

create trigger trg_alerts_updated_at
before update on alerts
for each row execute function set_updated_at();


-- ============================================================================
-- 9. reports  (saved / scheduled report definitions)
-- ============================================================================
create table reports (
    id           uuid primary key default gen_random_uuid(),
    report_type  text not null check (report_type in
                     ('case_volume', 'sla_compliance', 'alert_disposition',
                      'analyst_productivity', 'audit_trail')),
    filters      jsonb not null default '{}'::jsonb,
    cadence      text check (cadence in ('once', 'daily', 'weekly', 'monthly')),
    recipients   text[] not null default '{}',
    created_by   uuid not null references users(id) on delete restrict,
    last_run_at  timestamptz,
    next_run_at  timestamptz,
    created_at   timestamptz not null default now(),
    updated_at   timestamptz not null default now(),
    deleted_at   timestamptz
);

create index ix_reports_created_by  on reports (created_by) where deleted_at is null;
create index ix_reports_next_run_at on reports (next_run_at) where deleted_at is null and cadence <> 'once';

create trigger trg_reports_updated_at
before update on reports
for each row execute function set_updated_at();


-- ============================================================================
-- 10. audit_logs  (FR-SYS-3 — immutable record of sensitive reads and writes)
-- ============================================================================
create table audit_logs (
    id            uuid primary key default gen_random_uuid(),
    actor_id      uuid references users(id) on delete set null,
    action        text not null,
    resource_type text not null,
    resource_id   uuid not null,
    metadata      jsonb not null default '{}'::jsonb,
    ip_address    inet,
    created_at    timestamptz not null default now()
    -- no updated_at / deleted_at: insert-only, a correction is a new row, not an edit.
);

create index ix_audit_logs_resource   on audit_logs (resource_type, resource_id);
create index ix_audit_logs_actor_id   on audit_logs (actor_id);
create index ix_audit_logs_created_at on audit_logs (created_at);


-- ============================================================================
-- 11. refresh_tokens  (server-side revocation for the JWT refresh flow)
-- ============================================================================
create table refresh_tokens (
    id           uuid primary key default gen_random_uuid(),
    user_id      uuid not null references users(id) on delete cascade,
    token_hash   text not null unique,   -- sha256 of the token; the raw value is never stored
    expires_at   timestamptz not null,
    revoked_at   timestamptz,
    device_info  text,
    created_at   timestamptz not null default now(),
    updated_at   timestamptz not null default now()
);

create index ix_refresh_tokens_user_id on refresh_tokens (user_id);

create trigger trg_refresh_tokens_updated_at
before update on refresh_tokens
for each row execute function set_updated_at();

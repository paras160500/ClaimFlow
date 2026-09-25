-- ClaimFlow database schema (Supabase / PostgreSQL)
-- This is provided in Stage 1 so the synthetic data generator produces
-- rows that map 1:1 onto the real schema used later in Stage 3 (Node/Supabase).
-- Row Level Security + auth wiring will be added when we build the Node backend.

create extension if not exists "uuid-ossp";

-- ============================================================
-- CORE ENTITIES
-- ============================================================

create table if not exists repair_shops (
    id                  uuid primary key default uuid_generate_v4(),
    repair_shop_id      text unique not null,       -- e.g. RS0082
    name                text not null,
    city                text not null,
    registration_number text not null,
    created_at          timestamptz not null default now()
);

create table if not exists customers (
    id              uuid primary key default uuid_generate_v4(),
    customer_id     text unique not null,           -- e.g. C010243
    full_name       text not null,
    email           text not null,
    phone           text not null,
    date_of_birth   date not null,
    created_at      timestamptz not null default now()
);

create table if not exists vehicles (
    id                  uuid primary key default uuid_generate_v4(),
    vehicle_id          text unique not null,        -- e.g. V014412
    customer_id         text not null references customers(customer_id),
    make                text not null,
    model               text not null,
    manufacture_year    int not null,
    registration_number text not null,
    vehicle_value       numeric(12,2) not null,
    created_at          timestamptz not null default now()
);

create table if not exists policy_versions (
    id                  uuid primary key default uuid_generate_v4(),
    policy_version_id   text unique not null,        -- e.g. PV-COMP-V1
    policy_type         text not null,               -- COMPREHENSIVE, THIRD_PARTY, THEFT, COMMERCIAL
    version             text not null,               -- V1, V2
    effective_from      date not null,
    effective_to        date,
    description         text
);

create table if not exists policies (
    id                  uuid primary key default uuid_generate_v4(),
    policy_id           text unique not null,        -- e.g. P008821
    customer_id         text not null references customers(customer_id),
    vehicle_id          text not null references vehicles(vehicle_id),
    policy_type         text not null,
    policy_version_id   text not null references policy_versions(policy_version_id),
    coverage_limit      numeric(12,2) not null,
    deductible          numeric(12,2) not null,
    start_date          date not null,
    end_date            date not null,
    status              text not null default 'ACTIVE', -- ACTIVE, EXPIRED, CANCELLED
    created_at          timestamptz not null default now()
);

create table if not exists claims (
    id                      uuid primary key default uuid_generate_v4(),
    claim_id                text unique not null,     -- e.g. CL050001
    policy_id               text not null references policies(policy_id),
    customer_id             text not null references customers(customer_id),
    vehicle_id              text not null references vehicles(vehicle_id),
    repair_shop_id          text references repair_shops(repair_shop_id),
    claim_date              date not null,
    incident_date           date not null,
    claim_type              text not null,             -- ACCIDENT, THEFT, FIRE, NATURAL_DISASTER, VANDALISM
    claim_amount            numeric(12,2) not null,
    description             text,
    status                  text not null default 'SUBMITTED', -- SUBMITTED, UNDER_REVIEW, CLOSED
    investigation_status    text not null default 'NOT_FLAGGED', -- NOT_FLAGGED, FLAGGED, INVESTIGATED
    -- synthetic training label, generated for Stage 1 only, not exposed as "fraud":
    investigation_label     int,                       -- 0 = normal pattern, 1 = investigation pattern
    created_at              timestamptz not null default now()
);

create index if not exists idx_claims_policy on claims(policy_id);
create index if not exists idx_claims_customer on claims(customer_id);
create index if not exists idx_claims_vehicle on claims(vehicle_id);
create index if not exists idx_claims_repair_shop on claims(repair_shop_id);
create index if not exists idx_claims_claim_date on claims(claim_date);

-- ============================================================
-- INVESTIGATION / ML / AUDIT (populated in later stages)
-- ============================================================

create table if not exists employees (
    id              uuid primary key default uuid_generate_v4(),
    auth_user_id    uuid,
    name            text not null,
    email           text unique not null,
    role            text not null default 'INVESTIGATOR', -- ADMIN, INVESTIGATOR, REVIEWER
    department      text,
    created_at      timestamptz not null default now()
);

create table if not exists investigations (
    id                  uuid primary key default uuid_generate_v4(),
    investigation_id    text unique not null,
    claim_id            text not null references claims(claim_id),
    assigned_to         text references employees(email),
    status              text not null default 'OPEN', -- OPEN, IN_PROGRESS, CLOSED
    priority            text default 'MEDIUM',
    reason              text,
    investigator_notes  text,
    final_decision       text, -- APPROVE, REQUEST_DOCUMENTS, INVESTIGATE_FURTHER, REJECT
    created_at          timestamptz not null default now(),
    updated_at          timestamptz not null default now()
);

create table if not exists claim_documents (
    id              uuid primary key default uuid_generate_v4(),
    document_id     text unique not null,
    claim_id        text not null references claims(claim_id),
    document_type   text not null,
    file_name       text,
    storage_path    text,
    created_at      timestamptz not null default now()
);

create table if not exists ml_assessments (
    id                  uuid primary key default uuid_generate_v4(),
    claim_id            text not null references claims(claim_id),
    model_version       text not null,
    risk_probability    numeric(5,4) not null,
    risk_level          text not null, -- LOW, MEDIUM, HIGH
    features_json       jsonb,
    created_at          timestamptz not null default now()
);

create table if not exists risk_signals (
    id              uuid primary key default uuid_generate_v4(),
    claim_id        text not null references claims(claim_id),
    signal_type     text not null,
    severity        text not null, -- LOW, MEDIUM, HIGH
    description     text not null,
    source          text not null, -- RULES_ENGINE, ML_MODEL, RELATIONSHIP_ANALYSIS
    created_at      timestamptz not null default now()
);

create table if not exists audit_logs (
    id              uuid primary key default uuid_generate_v4(),
    employee_id     text,
    claim_id        text,
    action          text not null,
    details         text,
    created_at      timestamptz not null default now()
);

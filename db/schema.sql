-- Initial schema for the PhD opportunity tracker.

create table if not exists phd_opportunities (
    id bigserial primary key,
    external_id text not null,
    source_name text not null,
    source_url text not null,
    official_url text,
    verification_status text not null default 'aggregator_unverified',
    status text not null default 'active',

    title text not null,
    project_title text,
    institution text,
    department text,
    lab text,
    country text,
    city text,

    domain_primary text,
    domain_tags jsonb not null default '[]'::jsonb,

    supervisor_name text,
    supervisor_profile_url text,

    funding text,
    salary_stipend text,
    duration_text text,
    start_date_text text,
    deadline_text text,

    qualification_requirements text,
    required_documents jsonb not null default '[]'::jsonb,
    application_process text,

    description text,
    contact_info text,

    last_seen_at timestamptz,
    first_seen_at timestamptz default now(),
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);

create unique index if not exists phd_opportunities_source_external_id_idx
    on phd_opportunities (source_name, external_id);

create index if not exists phd_opportunities_status_idx
    on phd_opportunities (status);

create index if not exists phd_opportunities_country_idx
    on phd_opportunities (country);

create index if not exists phd_opportunities_domain_primary_idx
    on phd_opportunities (domain_primary);

create table if not exists phd_user_tracking (
    id bigserial primary key,
    opportunity_id bigint not null references phd_opportunities(id) on delete cascade,
    user_key text not null,
    is_applied boolean not null default false,
    applied_at timestamptz,
    notes text,
    documents_ready jsonb not null default '[]'::jsonb,
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);

create unique index if not exists phd_user_tracking_unique_idx
    on phd_user_tracking (opportunity_id, user_key);

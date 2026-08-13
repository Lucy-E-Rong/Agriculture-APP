create extension if not exists "pgcrypto";

create table organizations (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  subdomain text unique,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table profiles (
  id uuid primary key,
  org_id uuid not null references organizations(id) on delete cascade,
  full_name text not null,
  role text not null default 'scout' check (role in ('owner', 'admin', 'scout', 'viewer')),
  avatar_url text,
  preferred_language text not null default 'en' check (preferred_language in ('en', 'zh')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table greenhouses (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references organizations(id) on delete cascade,
  name text not null,
  short_id text not null,
  description text,
  size_m2 numeric,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (org_id, short_id)
);

create table sections (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references organizations(id) on delete cascade,
  greenhouse_id uuid not null references greenhouses(id) on delete cascade,
  name text not null,
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (greenhouse_id, name)
);

create table growing_tables (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references organizations(id) on delete cascade,
  section_id uuid not null references sections(id) on delete cascade,
  table_number integer not null check (table_number > 0),
  row_count integer not null check (row_count > 0),
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (section_id, table_number)
);

create table growing_rows (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references organizations(id) on delete cascade,
  table_id uuid not null references growing_tables(id) on delete cascade,
  row_number integer not null check (row_number > 0),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (table_id, row_number)
);

create table crop_types (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references organizations(id) on delete cascade,
  name text not null,
  variety text,
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (org_id, name, variety)
);

create table crops (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references organizations(id) on delete cascade,
  crop_type_id uuid references crop_types(id),
  row_id uuid not null references growing_rows(id),
  crop_name text not null,
  variety text,
  growth_stage text,
  planted_at date,
  status text not null default 'active' check (status in ('active', 'harvested', 'removed')),
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create unique index crops_one_active_per_row
  on crops(row_id)
  where status = 'active';

create table scans (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references organizations(id) on delete cascade,
  crop_id uuid references crops(id) on delete set null,
  greenhouse_id uuid references greenhouses(id) on delete set null,
  section_id uuid references sections(id) on delete set null,
  table_id uuid references growing_tables(id) on delete set null,
  row_id uuid references growing_rows(id) on delete set null,
  image_path text,
  ai_provider text not null default 'api_provider' check (ai_provider in ('api_provider', 'local_vlm')),
  language text not null default 'en' check (language in ('en', 'zh')),
  stress_level text not null check (stress_level in ('none', 'low', 'medium', 'high', 'critical')),
  severity_score integer not null check (severity_score between 0 and 5),
  confidence numeric not null check (confidence >= 0 and confidence <= 1),
  diagnosis text not null,
  detected_issues jsonb not null default '[]'::jsonb,
  recommendations jsonb not null default '[]'::jsonb,
  needs_human_review boolean not null default false,
  raw_model_response jsonb,
  created_by uuid references profiles(id),
  created_at timestamptz not null default now()
);

create table ai_settings (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references organizations(id) on delete cascade,
  default_provider text not null default 'api_provider' check (default_provider in ('api_provider', 'local_vlm')),
  default_language text not null default 'en' check (default_language in ('en', 'zh')),
  custom_prompt text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (org_id)
);

create index profiles_org_id_idx on profiles(org_id);
create index greenhouses_org_id_idx on greenhouses(org_id);
create index sections_org_id_greenhouse_idx on sections(org_id, greenhouse_id);
create index growing_tables_org_id_section_idx on growing_tables(org_id, section_id);
create index growing_rows_org_id_table_idx on growing_rows(org_id, table_id);
create index crops_org_id_row_idx on crops(org_id, row_id);
create index scans_org_id_created_at_idx on scans(org_id, created_at desc);
create index scans_org_id_stress_idx on scans(org_id, stress_level);

create or replace function set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create trigger organizations_set_updated_at before update on organizations for each row execute function set_updated_at();
create trigger profiles_set_updated_at before update on profiles for each row execute function set_updated_at();
create trigger greenhouses_set_updated_at before update on greenhouses for each row execute function set_updated_at();
create trigger sections_set_updated_at before update on sections for each row execute function set_updated_at();
create trigger growing_tables_set_updated_at before update on growing_tables for each row execute function set_updated_at();
create trigger growing_rows_set_updated_at before update on growing_rows for each row execute function set_updated_at();
create trigger crop_types_set_updated_at before update on crop_types for each row execute function set_updated_at();
create trigger crops_set_updated_at before update on crops for each row execute function set_updated_at();
create trigger ai_settings_set_updated_at before update on ai_settings for each row execute function set_updated_at();

create or replace function create_rows_for_table()
returns trigger
language plpgsql
as $$
begin
  insert into growing_rows(org_id, table_id, row_number)
  select new.org_id, new.id, generate_series(1, new.row_count)
  on conflict do nothing;
  return new;
end;
$$;

create trigger growing_tables_create_rows
after insert on growing_tables
for each row execute function create_rows_for_table();

alter table organizations enable row level security;
alter table profiles enable row level security;
alter table greenhouses enable row level security;
alter table sections enable row level security;
alter table growing_tables enable row level security;
alter table growing_rows enable row level security;
alter table crop_types enable row level security;
alter table crops enable row level security;
alter table scans enable row level security;
alter table ai_settings enable row level security;

create or replace function current_org_id()
returns uuid
language sql
security definer
stable
as $$
  select org_id from profiles where id = auth.uid()
$$;

create policy profiles_org_select on profiles for select using (org_id = current_org_id());
create policy profiles_org_update on profiles for update using (id = auth.uid()) with check (id = auth.uid());

create policy organizations_org_select on organizations for select using (id = current_org_id());

create policy greenhouses_org_all on greenhouses for all using (org_id = current_org_id()) with check (org_id = current_org_id());
create policy sections_org_all on sections for all using (org_id = current_org_id()) with check (org_id = current_org_id());
create policy growing_tables_org_all on growing_tables for all using (org_id = current_org_id()) with check (org_id = current_org_id());
create policy growing_rows_org_all on growing_rows for all using (org_id = current_org_id()) with check (org_id = current_org_id());
create policy crop_types_org_all on crop_types for all using (org_id = current_org_id()) with check (org_id = current_org_id());
create policy crops_org_all on crops for all using (org_id = current_org_id()) with check (org_id = current_org_id());
create policy scans_org_all on scans for all using (org_id = current_org_id()) with check (org_id = current_org_id());
create policy ai_settings_org_all on ai_settings for all using (org_id = current_org_id()) with check (org_id = current_org_id());


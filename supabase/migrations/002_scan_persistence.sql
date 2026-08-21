-- REQ-003 / REQ-005: persisted Demo scan history.
--
-- This migration intentionally keeps scan uploads separate from any future
-- expert-labelled training or evaluation dataset. The application backend must
-- use the Supabase service role; clients must never receive that credential.

alter table scans
  alter column org_id drop not null;

alter table scans
  drop constraint if exists scans_ai_provider_check;

alter table scans
  add constraint scans_ai_provider_check
  check (ai_provider in ('gemini', 'api_provider', 'local_vlm', 'mock'));

alter table scans
  add column if not exists status text not null default 'succeeded',
  add column if not exists data_stage text not null default 'demo',
  add column if not exists data_purpose text not null default 'user_upload',
  add column if not exists image_mime_type text not null default 'image/jpeg',
  add column if not exists image_size_bytes integer,
  add column if not exists location_snapshot jsonb not null default '{}'::jsonb,
  add column if not exists analysis_result jsonb,
  add column if not exists analysis_schema_version text not null default '1',
  add column if not exists model_name text;

alter table scans
  add constraint scans_status_check
  check (status = 'succeeded'),
  add constraint scans_data_stage_check
  check (data_stage in ('demo', 'test', 'production')),
  add constraint scans_data_purpose_check
  check (data_purpose = 'user_upload'),
  add constraint scans_image_mime_type_check
  check (image_mime_type = 'image/jpeg'),
  add constraint scans_image_size_bytes_check
  check (image_size_bytes is null or image_size_bytes > 0),
  add constraint scans_image_path_required_check
  check (image_path is not null and length(btrim(image_path)) > 0),
  add constraint scans_analysis_result_required_check
  check (analysis_result is not null and jsonb_typeof(analysis_result) = 'object'),
  add constraint scans_location_snapshot_object_check
  check (jsonb_typeof(location_snapshot) = 'object');

comment on table scans is
  'Successful FarmScout product scans. User uploads are not training or evaluation data.';
comment on column scans.data_stage is
  'Lifecycle stage for grouped filtering/deletion; current writes use demo.';
comment on column scans.data_purpose is
  'Purpose boundary. user_upload must never be treated as expert-labelled training data.';
comment on column scans.analysis_result is
  'Complete validated AnalyzeScanResponse JSON used to reopen scan details.';
comment on column scans.image_path is
  'Private scan-images object path. Store the compressed JPEG actually submitted to the model.';

create index if not exists scans_stage_status_created_at_idx
  on scans(data_stage, status, created_at desc);

create index if not exists scans_purpose_created_at_idx
  on scans(data_purpose, created_at desc);

-- Storage is private. Uploads, signed reads, and deletions are backend-only in
-- the current shared-access-code Demo, so no anon/authenticated object policies
-- are created here. The service role bypasses Storage RLS.
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values (
  'scan-images',
  'scan-images',
  false,
  5000000,
  array['image/jpeg']::text[]
)
on conflict (id) do update
set public = false,
    file_size_limit = excluded.file_size_limit,
    allowed_mime_types = excluded.allowed_mime_types;

-- Group deletion is deliberately database-only. The backend must first delete
-- the exact image paths through the Storage API, then call this function with
-- the matching IDs. If database deletion fails, retrying is safe: rows remain
-- visible as evidence, while no untracked image object is left behind.
create or replace function delete_demo_user_upload_scan_records(p_scan_ids uuid[])
returns table (deleted_id uuid)
language sql
security invoker
set search_path = public
as $$
  delete from scans
  where id = any(p_scan_ids)
    and data_stage = 'demo'
    and data_purpose = 'user_upload'
  returning id
$$;

revoke all on function delete_demo_user_upload_scan_records(uuid[]) from public;
revoke all on function delete_demo_user_upload_scan_records(uuid[]) from anon;
revoke all on function delete_demo_user_upload_scan_records(uuid[]) from authenticated;
grant execute on function delete_demo_user_upload_scan_records(uuid[]) to service_role;

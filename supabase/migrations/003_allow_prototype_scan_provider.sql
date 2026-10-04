-- Keep the persisted provider provenance aligned with the five providers that
-- AnalyzeScanRequest currently accepts. This changes only the existing CHECK;
-- no scan row, column, JSON payload, RLS policy, or other constraint is changed.

begin;

-- Preserve the current constraint while the replacement is created and checked
-- against every historical row. The transaction prevents an externally visible
-- constraint gap when the names are swapped.
alter table public.scans
  drop constraint if exists scans_ai_provider_check_v2;

alter table public.scans
  add constraint scans_ai_provider_check_v2
  check (ai_provider in ('gemini', 'prototype', 'api_provider', 'local_vlm', 'mock'))
  not valid;

alter table public.scans
  validate constraint scans_ai_provider_check_v2;

alter table public.scans
  drop constraint if exists scans_ai_provider_check;

alter table public.scans
  rename constraint scans_ai_provider_check_v2 to scans_ai_provider_check;

commit;

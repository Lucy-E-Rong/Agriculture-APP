-- Prototype responses are ordinary text, not FarmScout assessments. Keep the
-- FarmScout summary columns for structured scans, but allow them to be absent
-- for a persisted Prototype response whose complete text lives in
-- analysis_result.

begin;

alter table public.scans
  alter column stress_level drop not null,
  alter column severity_score drop not null,
  alter column confidence drop not null,
  alter column diagnosis drop not null;

commit;

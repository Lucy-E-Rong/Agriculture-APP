# Supabase Setup

Apply migrations in `supabase/migrations` to a Supabase Postgres project.

## Storage

Create a private bucket:

```text
scan-images
```

Recommended object path:

```text
org/{org_id}/scans/{scan_id}.jpg
```

The backend should upload images with the Supabase service role key. The mobile app should not receive the service role key.

## Notes

- The schema uses `growing_tables` instead of `tables` because `tables` is easy to confuse with SQL/system naming.
- `growing_tables_create_rows` auto-creates row records when a table is inserted.
- `crops_one_active_per_row` prevents two active crops from being assigned to the same row.
- RLS is included for Supabase client access, but the recommended first implementation routes app traffic through FastAPI.


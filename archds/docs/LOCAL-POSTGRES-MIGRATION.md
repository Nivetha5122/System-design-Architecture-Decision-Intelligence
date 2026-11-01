# ARCHDS V7.2 Local PostgreSQL migration notes

This release is designed to start against the existing `architecture_db` database without requiring Docker or `psql.exe` in PATH.

The previous database schema could contain legacy columns that conflicted with the newer JPA model:
- `requirements.alternatives` and `requirements.max_iterations` could contain NULL values while Hibernate attempted to add NOT NULL constraints.
- `verification_results.issues_json` could be mapped as PostgreSQL `oid` by the old `@Lob` mapping.
- older `users` tables could contain a required `updated_at` column while the Java entity did not populate it.

V7.2 addresses these in the entity model:
- alternatives/max_iterations are nullable-compatible and the analysis service supplies defaults when values are missing.
- verification JSON is stored as PostgreSQL TEXT.
- users now manage `updated_at` automatically on insert/update.

No data reset is required for these fixes. If your database contains unrelated schema damage from an older build, back it up before manually changing tables.

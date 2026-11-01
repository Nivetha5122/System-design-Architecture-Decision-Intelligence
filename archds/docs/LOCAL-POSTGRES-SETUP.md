# ARCHDS Local PostgreSQL Setup

The no-Docker Windows launcher uses the existing local PostgreSQL database supplied for ARCHDS.

- Host: `localhost`
- Port: `5432`
- Database: `architecture_db`
- User: `architecture_user`
- Password: `host`

## Verify with PostgreSQL SQL Shell

Connect using SQL Shell (psql), then run:

```sql
\c architecture_db
\dt
```

If the database is empty, that is expected on first launch. Spring Boot/JPA creates or updates the ARCHDS tables with `ddl-auto: update`.

If the user exists but its password is different, run as a PostgreSQL administrator:

```sql
ALTER USER architecture_user WITH PASSWORD 'host';
```

## Start without Docker

From the `archds-platform` directory:

```cmd
scripts\START-NO-DOCKER.cmd
```

The launcher checks TCP port 5432 using PowerShell, so `psql.exe` does not need to be in the Windows PATH.

The backend explicitly starts with the `postgres` profile and the connection values above.

## Inspect the data

After ARCHDS starts and you create/run an analysis:

```sql
\c architecture_db
\dt
SELECT * FROM users;
SELECT * FROM projects;
SELECT * FROM requirements;
```

## Docker

Docker Compose remains available as a separate deployment mode. Its PostgreSQL container keeps its own `archds` database/user defaults and is not mixed with the local PostgreSQL setup.

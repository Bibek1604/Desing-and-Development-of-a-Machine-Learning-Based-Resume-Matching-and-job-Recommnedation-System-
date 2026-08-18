"""One-shot data transfer from the legacy SQLite file into PostgreSQL.

The project now runs on PostgreSQL only (see config.settings). This command
moves the existing development dataset across so the evaluation figures
reported in the thesis can be reproduced against the new database.

    python manage.py migrate_sqlite_to_postgres --sqlite db.sqlite3

It copies application tables only. Django's own bookkeeping tables
(django_migrations, django_content_type, auth_permission) are rebuilt by
``migrate`` and are deliberately not copied — copying them produces primary-key
collisions against the rows ``migrate`` has already created.

Safe to re-run: each table is truncated before it is filled.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction

# Foreign-key-safe order: a table only ever appears after everything it
# references. Truncation walks this list backwards.
TABLES = [
    "skills_skill",
    "accounts_user",
    "accounts_candidateprofile",
    "accounts_employerprofile",
    "accounts_candidateprofile_skills",
    "jobs_job",
    "jobs_job_required_skills",
    "resumes_resume",
    "resumes_resume_extracted_skills",
    "accounts_atsanalysis",
    "accounts_candidateembedding",
    "accounts_careerrecommendation",
    "accounts_skillgapreport",
    "applications_application",
    "applications_recommendationfeedback",
    "applications_savedjob",
    "notifications_notification",
    "notifications_emaillog",
    "matching_modelversion",
]

BATCH = 5000


def _pg_columns(cur, table):
    """{column_name: data_type} for a table in the target database."""
    cur.execute(
        "SELECT column_name, data_type FROM information_schema.columns "
        "WHERE table_schema = 'public' AND table_name = %s",
        [table],
    )
    return {r[0]: r[1] for r in cur.fetchall()}


def _coerce(value, pg_type):
    """SQLite stores booleans as 0/1 and JSON as text; PostgreSQL is strict."""
    if value is None:
        return None
    if pg_type == "boolean":
        return bool(value) if isinstance(value, bool) else bool(int(value))
    if pg_type in ("json", "jsonb"):
        if isinstance(value, (dict, list)):
            return json.dumps(value)
        return value  # already a JSON string from SQLite
    return value


class Command(BaseCommand):
    help = "Copy application data from the legacy SQLite file into PostgreSQL."

    def add_arguments(self, parser):
        parser.add_argument("--sqlite", default="db.sqlite3",
                            help="Path to the source SQLite file.")
        parser.add_argument("--dry-run", action="store_true",
                            help="Report row counts without writing anything.")

    def handle(self, *args, **opts):
        if connection.vendor != "postgresql":
            raise CommandError(
                f"Target database is '{connection.vendor}', expected 'postgresql'. "
                "Check DB_* settings in .env."
            )
        src_path = Path(opts["sqlite"])
        if not src_path.exists():
            raise CommandError(f"SQLite file not found: {src_path.resolve()}")

        src = sqlite3.connect(str(src_path))
        src.row_factory = sqlite3.Row
        sqlite_tables = {
            r[0] for r in src.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }

        summary = []
        with connection.cursor() as cur:
            present = [t for t in TABLES if t in sqlite_tables]
            missing = [t for t in TABLES if t not in sqlite_tables]
            for t in missing:
                self.stdout.write(self.style.WARNING(f"  skip {t} (absent from SQLite)"))

            if opts["dry_run"]:
                for t in present:
                    n = src.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
                    self.stdout.write(f"  {n:>8,}  {t}")
                return

            with transaction.atomic():
                # Truncate in reverse dependency order. RESTART IDENTITY resets
                # the sequences; CASCADE covers anything not in the list.
                cur.execute(
                    "TRUNCATE {} RESTART IDENTITY CASCADE".format(
                        ", ".join(f'"{t}"' for t in reversed(present))
                    )
                )

                for table in present:
                    types = _pg_columns(cur, table)
                    rows = src.execute(f'SELECT * FROM "{table}"')
                    cols = [d[0] for d in rows.description]
                    cols = [c for c in cols if c in types]
                    if not cols:
                        continue
                    collist = ", ".join(f'"{c}"' for c in cols)
                    ph = ", ".join(["%s"] * len(cols))
                    sql = f'INSERT INTO "{table}" ({collist}) VALUES ({ph})'

                    total = 0
                    batch = []
                    for row in rows:
                        batch.append(tuple(_coerce(row[c], types[c]) for c in cols))
                        if len(batch) >= BATCH:
                            cur.executemany(sql, batch)
                            total += len(batch)
                            batch = []
                    if batch:
                        cur.executemany(sql, batch)
                        total += len(batch)

                    summary.append((table, total))
                    self.stdout.write(f"  {total:>8,}  {table}")

                # Realign every sequence with the highest id actually present,
                # otherwise the next INSERT reuses id 1 and fails the PK check.
                for table, _ in summary:
                    cur.execute(
                        "SELECT setval(pg_get_serial_sequence(%s, 'id'), "
                        "COALESCE((SELECT MAX(id) FROM \"%s\"), 1), true)"
                        % ("%s", table),
                        [table],
                    )

        src.close()
        self.stdout.write(self.style.SUCCESS(
            f"\nTransferred {sum(n for _, n in summary):,} rows across {len(summary)} tables."
        ))

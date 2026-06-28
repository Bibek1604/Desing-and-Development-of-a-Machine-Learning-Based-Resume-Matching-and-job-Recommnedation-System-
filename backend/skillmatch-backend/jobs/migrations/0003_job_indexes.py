from django.db import migrations, models


class Migration(migrations.Migration):
    """Indexes for the hot job-list query paths (is_active filter, type and
    location filters, newest-first ordering) — added after seeding ~5k jobs."""

    dependencies = [
        ("jobs", "0002_job_requirements_salary"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="job",
            index=models.Index(fields=["is_active", "-posted_at"], name="job_active_posted_idx"),
        ),
        migrations.AddIndex(
            model_name="job",
            index=models.Index(fields=["job_type"], name="job_type_idx"),
        ),
        migrations.AddIndex(
            model_name="job",
            index=models.Index(fields=["location"], name="job_location_idx"),
        ),
    ]

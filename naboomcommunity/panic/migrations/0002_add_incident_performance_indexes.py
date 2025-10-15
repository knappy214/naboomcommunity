# Generated manually for AIC-14 Database Connection Pooling & Query Optimization
# This migration adds critical performance indexes for panic incidents

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('panic', '0001_initial'),
    ]

    operations = [
        # Add performance indexes for panic incidents as specified in AIC-14
        # Using separate operations for CONCURRENTLY to avoid transaction block errors
        migrations.RunSQL(
            # Create index for incidents by status and creation date for emergency response
            "CREATE INDEX IF NOT EXISTS idx_incidents_status_created ON panic_incident (status, created_at DESC);",
            reverse_sql="DROP INDEX IF EXISTS idx_incidents_status_created;"
        ),
        migrations.RunSQL(
            # Create index for incidents by priority and status for triage operations
            "CREATE INDEX IF NOT EXISTS idx_incidents_priority_status ON panic_incident (priority, status);",
            reverse_sql="DROP INDEX IF EXISTS idx_incidents_priority_status;"
        ),
        migrations.RunSQL(
            # Create index for incidents by reporter and creation date for user history
            "CREATE INDEX IF NOT EXISTS idx_incidents_reported_by_created ON panic_incident (reported_by_id, created_at DESC);",
            reverse_sql="DROP INDEX IF EXISTS idx_incidents_reported_by_created;"
        ),
        migrations.RunSQL(
            # Create index for incidents by client and status for client management
            "CREATE INDEX IF NOT EXISTS idx_incidents_client_status ON panic_incident (client_id, status) WHERE client_id IS NOT NULL;",
            reverse_sql="DROP INDEX IF EXISTS idx_incidents_client_status;"
        ),
    ]

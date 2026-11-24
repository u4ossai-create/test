"""Prepare the temporary SQLite copy used on Vercel when no DATABASE_URL is set.

The Attendance model is unmanaged (it maps to an existing PostgreSQL table), so
migrations never create it. Without a hosted database we create it here so the
app can run; all data is discarded when the function instance is recycled.
"""

from django.conf import settings
from django.db import connection


def ensure_tables():
    if not getattr(settings, "USING_EPHEMERAL_SQLITE", False):
        return

    from attendance.models import Attendance

    if Attendance._meta.db_table not in connection.introspection.table_names():
        with connection.schema_editor() as editor:
            editor.create_model(Attendance)

#!/usr/bin/env bash

set -o errexit

echo "======================================"
echo " DIGITAL GALLERIA - RENDER BUILD"
echo "======================================"

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Checking Django..."
python manage.py check

echo "Collecting static files..."
python manage.py collectstatic --no-input

echo "======================================"
echo " CHECKING / REPAIRING DATABASE SCHEMA"
echo "======================================"

python manage.py shell <<'PY'
from django.db import connection
from django.db.migrations.loader import MigrationLoader

table_name = "coupons_couponusage"

with connection.cursor() as cursor:
    tables = connection.introspection.table_names()

if table_name not in tables:
    print(f"WARNING: {table_name} is missing.")
    print("Creating CouponUsage table from coupons.0001_initial...")

    loader = MigrationLoader(
        connection,
        ignore_no_migrations=True,
    )

    state = loader.project_state(
        [("coupons", "0001_initial")]
    )

    CouponUsage = state.apps.get_model(
        "coupons",
        "CouponUsage",
    )

    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(CouponUsage)

    print(f"SUCCESS: {table_name} created.")
else:
    print(f"OK: {table_name} already exists.")

PY

echo "======================================"
echo " MIGRATION STATUS"
echo "======================================"

python manage.py showmigrations coupons
python manage.py showmigrations customization
python manage.py showmigrations accounts

echo "======================================"
echo " RUNNING DATABASE MIGRATIONS"
echo "======================================"

python manage.py migrate --noinput

echo "======================================"
echo " BUILD COMPLETED SUCCESSFULLY"
echo "======================================"
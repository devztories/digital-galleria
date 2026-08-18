#!/usr/bin/env bash

set -o errexit

echo "======================================"
echo " DIGITAL GALLERIA - RENDER BUILD"
echo "======================================"

echo "Installing dependencies..."
pip install -r requirements.txt

echo "======================================"
echo " CHECKING DJANGO"
echo "======================================"

python manage.py check

echo "======================================"
echo " COLLECTING STATIC FILES"
echo "======================================"

python manage.py collectstatic --no-input

echo "======================================"
echo " CHECKING / REPAIRING DATABASE SCHEMA"
echo "======================================"

python manage.py shell <<'PY'
from django.db import connection
from django.db.migrations.loader import MigrationLoader

print("Checking database schema...")

tables = connection.introspection.table_names()

# ============================================================
# COUPONS
# ============================================================

coupon_usage_table = "coupons_couponusage"

print("")
print("---- COUPONS ----")

if coupon_usage_table not in tables:
    print(f"WARNING: {coupon_usage_table} is missing.")
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

    print(f"SUCCESS: {coupon_usage_table} created.")

else:
    print(f"OK: {coupon_usage_table} already exists.")


# ============================================================
# CUSTOMIZATION
# ============================================================

customization_table = "customization_customization"
customization_image_table = "customization_customizationimage"

print("")
print("---- CUSTOMIZATION ----")

print(
    "Customization table exists:",
    customization_table in tables
)

print(
    "CustomizationImage table exists:",
    customization_image_table in tables
)

if customization_table in tables:

    with connection.cursor() as cursor:

        columns = [
            col.name
            for col in connection.introspection.get_table_description(
                cursor,
                customization_table
            )
        ]

    print("")
    print("Customization columns:")

    for column in columns:
        print(" -", column)

    print("")
    print("Customization data count:")

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f'SELECT COUNT(*) FROM "{customization_table}"'
            )
            count = cursor.fetchone()[0]

        print("Customization records:", count)

    except Exception as exc:
        print("Could not count customization records:", exc)


if customization_image_table in tables:

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f'SELECT COUNT(*) FROM "{customization_image_table}"'
            )
            image_count = cursor.fetchone()[0]

        print(
            "CustomizationImage records:",
            image_count
        )

    except Exception as exc:
        print(
            "Could not count CustomizationImage records:",
            exc
        )


# ============================================================
# ACCOUNTS
# ============================================================

accounts_table = "accounts_user"

print("")
print("---- ACCOUNTS ----")

print(
    "Accounts user table exists:",
    accounts_table in tables
)

if accounts_table in tables:

    with connection.cursor() as cursor:

        columns = [
            col.name
            for col in connection.introspection.get_table_description(
                cursor,
                accounts_table
            )
        ]

    print("Accounts columns:")

    for column in columns:
        print(" -", column)

PY


echo "======================================"
echo " MIGRATION STATUS BEFORE REPAIR"
echo "======================================"

echo ""
echo "COUPONS:"
python manage.py showmigrations coupons

echo ""
echo "CUSTOMIZATION:"
python manage.py showmigrations customization

echo ""
echo "ACCOUNTS:"
python manage.py showmigrations accounts


echo "======================================"
echo " CHECKING CUSTOMIZATION MIGRATION"
echo "======================================"

python manage.py shell <<'PY'
from django.db import connection
from django.db.migrations.recorder import MigrationRecorder

customization_table = "customization_customization"

with connection.cursor() as cursor:

    tables = connection.introspection.table_names()

    if customization_table not in tables:
        print(
            "Customization table does not exist."
        )

    else:

        columns = [
            col.name
            for col in connection.introspection.get_table_description(
                cursor,
                customization_table
            )
        ]

        print(
            "Existing customization columns:"
        )

        for column in columns:
            print(" -", column)

        existing_migration = (
            MigrationRecorder(connection)
            .migration_qs
            .filter(
                app="customization",
                name="0002_customization_via_whatsapp_and_more"
            )
            .exists()
        )

        has_via_whatsapp = (
            "via_whatsapp" in columns
        )

        has_whatsapp_message = (
            "whatsapp_message" in columns
        )

        has_customization_image = (
            "customization_customizationimage"
            in tables
        )

        print("")
        print(
            "Migration 0002 recorded:",
            existing_migration
        )

        print(
            "via_whatsapp exists:",
            has_via_whatsapp
        )

        print(
            "whatsapp_message exists:",
            has_whatsapp_message
        )

        print(
            "CustomizationImage exists:",
            has_customization_image
        )

        # ----------------------------------------------------
        # If database already contains the schema created by
        # migration 0002, mark migration as applied.
        # ----------------------------------------------------

        if (
            not existing_migration
            and has_via_whatsapp
            and has_whatsapp_message
            and has_customization_image
        ):

            print("")
            print(
                "Existing database already contains "
                "Customization migration 0002 schema."
            )

            print(
                "Marking customization.0002 as applied..."
            )

            MigrationRecorder(connection).record_applied(
                "customization",
                "0002_customization_via_whatsapp_and_more"
            )

            print(
                "SUCCESS: customization.0002 marked as applied."
            )

PY


echo "======================================"
echo " CHECKING ACCOUNTS MIGRATION"
echo "======================================"

python manage.py shell <<'PY'
from django.db import connection
from django.db.migrations.recorder import MigrationRecorder

accounts_table = "accounts_user"

with connection.cursor() as cursor:

    tables = connection.introspection.table_names()

    if accounts_table not in tables:
        print(
            "Accounts table does not exist."
        )

    else:

        columns = [
            col.name
            for col in connection.introspection.get_table_description(
                cursor,
                accounts_table
            )
        ]

        print("Existing accounts columns:")

        for column in columns:
            print(" -", column)

        migration_exists = (
            MigrationRecorder(connection)
            .migration_qs
            .filter(
                app="accounts",
                name="0002_alter_user_theme_preference"
            )
            .exists()
        )

        has_theme_preference = (
            "theme_preference" in columns
        )

        print("")
        print(
            "accounts.0002 recorded:",
            migration_exists
        )

        print(
            "theme_preference exists:",
            has_theme_preference
        )

        # If the column already exists in the database,
        # mark the migration as applied.
        if (
            not migration_exists
            and has_theme_preference
        ):

            print("")
            print(
                "theme_preference already exists."
            )

            print(
                "Marking accounts.0002 as applied..."
            )

            MigrationRecorder(connection).record_applied(
                "accounts",
                "0002_alter_user_theme_preference"
            )

            print(
                "SUCCESS: accounts.0002 marked as applied."
            )

PY


echo "======================================"
echo " FINAL MIGRATION STATUS"
echo "======================================"

echo ""
echo "COUPONS:"
python manage.py showmigrations coupons

echo ""
echo "CUSTOMIZATION:"
python manage.py showmigrations customization

echo ""
echo "ACCOUNTS:"
python manage.py showmigrations accounts


echo "======================================"
echo " RUNNING DATABASE MIGRATIONS"
echo "======================================"

python manage.py migrate --noinput


echo "======================================"
echo " FINAL DJANGO CHECK"
echo "======================================"

python manage.py check


echo "======================================"
echo " BUILD COMPLETED SUCCESSFULLY"
echo "======================================"
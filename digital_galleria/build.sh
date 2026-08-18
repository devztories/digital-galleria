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
echo " DATABASE SCHEMA REPAIR"
echo "======================================"

python manage.py shell <<'PY'

from django.db import connection
from django.db.migrations.loader import MigrationLoader
from django.db.migrations.recorder import MigrationRecorder


# ============================================================
# HELPER
# ============================================================

def get_columns(table_name):
    with connection.cursor() as cursor:
        return [
            column.name
            for column in connection.introspection.get_table_description(
                cursor,
                table_name
            )
        ]


def get_tables():
    return connection.introspection.table_names()


def migration_exists(app, name):
    return MigrationRecorder(connection).migration_qs.filter(
        app=app,
        name=name
    ).exists()


def mark_migration(app, name):
    recorder = MigrationRecorder(connection)

    if not migration_exists(app, name):
        recorder.record_applied(app, name)
        print(
            f"SUCCESS: Marked {app}.{name} as applied."
        )
    else:
        print(
            f"OK: {app}.{name} already recorded."
        )


print("")
print("======================================")
print(" DATABASE SCHEMA STATUS")
print("======================================")


tables = get_tables()


# ============================================================
# 1. COUPONS
# ============================================================

print("")
print("---- COUPONS ----")

coupon_usage_table = "coupons_couponusage"

if coupon_usage_table not in tables:

    print(
        "WARNING: coupons_couponusage is missing."
    )

    print(
        "Creating CouponUsage from coupons.0001_initial..."
    )

    loader = MigrationLoader(
        connection,
        ignore_no_migrations=True
    )

    state = loader.project_state(
        [("coupons", "0001_initial")]
    )

    CouponUsage = state.apps.get_model(
        "coupons",
        "CouponUsage"
    )

    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(CouponUsage)

    print(
        "SUCCESS: coupons_couponusage created."
    )

else:

    print(
        "OK: coupons_couponusage already exists."
    )


# ============================================================
# 2. CUSTOMIZATION
# ============================================================

print("")
print("---- CUSTOMIZATION ----")

customization_table = "customization_customization"
customization_image_table = "customization_customizationimage"

tables = get_tables()

if customization_table not in tables:

    print(
        "ERROR: customization_customization table is missing."
    )

else:

    columns = get_columns(
        customization_table
    )

    print(
        "Current customization columns:"
    )

    for column in columns:
        print(
            " -",
            column
        )

    print("")
    print(
        "Customization records:"
    )

    try:

        with connection.cursor() as cursor:

            cursor.execute(
                f'SELECT COUNT(*) FROM "{customization_table}"'
            )

            count = cursor.fetchone()[0]

        print(
            count
        )

    except Exception as exc:

        print(
            "Could not count customization records:",
            exc
        )


# ------------------------------------------------------------
# Add via_whatsapp if missing
# ------------------------------------------------------------

    if "via_whatsapp" not in columns:

        print("")
        print(
            "Adding missing via_whatsapp column..."
        )

        with connection.cursor() as cursor:

            cursor.execute(
                """
                ALTER TABLE customization_customization
                ADD COLUMN via_whatsapp BOOLEAN NOT NULL DEFAULT FALSE
                """
            )

        print(
            "SUCCESS: via_whatsapp added."
        )

    else:

        print(
            "OK: via_whatsapp already exists."
        )


# ------------------------------------------------------------
# Add whatsapp_message if missing
# ------------------------------------------------------------

    columns = get_columns(
        customization_table
    )

    if "whatsapp_message" not in columns:

        print("")
        print(
            "Adding missing whatsapp_message column..."
        )

        with connection.cursor() as cursor:

            cursor.execute(
                """
                ALTER TABLE customization_customization
                ADD COLUMN whatsapp_message TEXT NOT NULL DEFAULT ''
                """
            )

        print(
            "SUCCESS: whatsapp_message added."
        )

    else:

        print(
            "OK: whatsapp_message already exists."
        )


# ------------------------------------------------------------
# CustomizationImage
# ------------------------------------------------------------

    tables = get_tables()

    if customization_image_table in tables:

        print(
            "OK: customization_customizationimage already exists."
        )

    else:

        print(
            "WARNING: customization_customizationimage is missing."
        )

        print(
            "Creating CustomizationImage table..."
        )

        loader = MigrationLoader(
            connection,
            ignore_no_migrations=True
        )

        state = loader.project_state(
            [(
                "customization",
                "0002_customization_via_whatsapp_and_more"
            )]
        )

        CustomizationImage = state.apps.get_model(
            "customization",
            "CustomizationImage"
        )

        with connection.schema_editor() as schema_editor:

            schema_editor.create_model(
                CustomizationImage
            )

        print(
            "SUCCESS: CustomizationImage created."
        )


# ------------------------------------------------------------
# Mark customization migration as applied
# ------------------------------------------------------------

    tables = get_tables()
    columns = get_columns(
        customization_table
    )

    customization_ready = (
        "via_whatsapp" in columns
        and
        "whatsapp_message" in columns
        and
        customization_image_table in tables
    )

    customization_migration = (
        "0002_customization_via_whatsapp_and_more"
    )

    if customization_ready:

        print("")
        print(
            "Customization database schema is ready."
        )

        if not migration_exists(
            "customization",
            customization_migration
        ):

            print(
                "Recording customization.0002..."
            )

            mark_migration(
                "customization",
                customization_migration
            )

        else:

            print(
                "OK: customization.0002 already recorded."
            )

    else:

        print(
            "ERROR: Customization schema is incomplete."
        )
        raise SystemExit(1)


# ============================================================
# 3. ACCOUNTS
# ============================================================

print("")
print("---- ACCOUNTS ----")

accounts_table = "accounts_user"

tables = get_tables()

if accounts_table not in tables:

    print(
        "ERROR: accounts_user table is missing."
    )

else:

    columns = get_columns(
        accounts_table
    )

    print(
        "Current accounts columns:"
    )

    for column in columns:
        print(
            " -",
            column
        )


# ------------------------------------------------------------
# theme_preference
# ------------------------------------------------------------

    if "theme_preference" not in columns:

        print("")
        print(
            "WARNING: theme_preference is missing."
        )

        print(
            "Adding theme_preference..."
        )

        with connection.cursor() as cursor:

            cursor.execute(
                """
                ALTER TABLE accounts_user
                ADD COLUMN theme_preference VARCHAR(10)
                NOT NULL DEFAULT 'system'
                """
            )

        print(
            "SUCCESS: theme_preference added."
        )

    else:

        print(
            "OK: theme_preference already exists."
        )


# ------------------------------------------------------------
# Record accounts migration
# ------------------------------------------------------------

    accounts_migration = (
        "0002_alter_user_theme_preference"
    )

    columns = get_columns(
        accounts_table
    )

    if "theme_preference" in columns:

        if not migration_exists(
            "accounts",
            accounts_migration
        ):

            print("")
            print(
                "Recording accounts.0002..."
            )

            mark_migration(
                "accounts",
                accounts_migration
            )

        else:

            print(
                "OK: accounts.0002 already recorded."
            )


# ============================================================
# FINAL DATABASE STATUS
# ============================================================

print("")
print("======================================")
print(" DATABASE REPAIR COMPLETED")
print("======================================")

print("")
print("Coupons table:")
print(
    "coupons_couponusage exists:",
    "coupons_couponusage" in get_tables()
)

print("")
print("Customization table:")
print(
    "customization_customization exists:",
    "customization_customization" in get_tables()
)

if "customization_customization" in get_tables():

    final_columns = get_columns(
        "customization_customization"
    )

    print(
        "via_whatsapp:",
        "via_whatsapp" in final_columns
    )

    print(
        "whatsapp_message:",
        "whatsapp_message" in final_columns
    )

print("")
print("CustomizationImage table:")
print(
    "customization_customizationimage exists:",
    "customization_customizationimage"
    in get_tables()
)

print("")
print("Accounts theme_preference:")
print(
    "theme_preference exists:",
    "theme_preference"
    in get_columns("accounts_user")
    if "accounts_user" in get_tables()
    else False
)

PY


echo "======================================"
echo " MIGRATION STATUS"
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
echo " RUNNING REMAINING MIGRATIONS"
echo "======================================"

python manage.py migrate --noinput


echo "======================================"
echo " FINAL DJANGO CHECK"
echo "======================================"

python manage.py check


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
echo " BUILD COMPLETED SUCCESSFULLY"
echo "======================================"
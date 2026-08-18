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
echo " REPAIRING EXISTING DATABASE SCHEMA"
echo "======================================"

python manage.py shell <<'PY'
from django.db import connection
from django.utils import timezone
from django.db import models

print("Checking existing database schema...")

# ============================================================
# ACCOUNTS
# ============================================================

print("")
print("---- ACCOUNTS ----")

with connection.cursor() as cursor:
    tables = connection.introspection.table_names()

if "accounts_user" not in tables:
    print("accounts_user table does not exist.")
    print("It will be created by Django migrations.")
else:
    with connection.cursor() as cursor:
        columns = {
            col.name
            for col in connection.introspection.get_table_description(
                cursor,
                "accounts_user"
            )
        }

    print("Existing accounts_user columns:")
    for column in sorted(columns):
        print(" -", column)

    from accounts.models import User

    fields_to_repair = [
        "theme_preference",
        "preferred_vehicle",
        "created_date",
        "updated_date",
    ]

    for field_name in fields_to_repair:

        if field_name in columns:
            print(f"OK: accounts_user.{field_name} already exists.")
            continue

        print("")
        print(f"REPAIRING: accounts_user.{field_name}")

        original_field = User._meta.get_field(field_name)
        repair_field = original_field.clone()

        # Existing rows may already exist, so first create the
        # column as nullable.
        repair_field.null = True
        repair_field.default = None

        with connection.schema_editor() as schema_editor:
            schema_editor.add_field(User, repair_field)

        print(f"Created nullable column: {field_name}")

    # Refresh columns after adding missing fields.
    with connection.cursor() as cursor:
        columns = {
            col.name
            for col in connection.introspection.get_table_description(
                cursor,
                "accounts_user"
            )
        }

    # --------------------------------------------------------
    # Fill missing values
    # --------------------------------------------------------

    now = timezone.now()

    if "theme_preference" in columns:
        updated = User.objects.filter(
            theme_preference__isnull=True
        ).update(
            theme_preference="system"
        )
        print(
            f"theme_preference repaired: {updated} existing rows"
        )

    if "preferred_vehicle" in columns:
        updated = User.objects.filter(
            preferred_vehicle__isnull=True
        ).update(
            preferred_vehicle="bike"
        )
        print(
            f"preferred_vehicle repaired: {updated} existing rows"
        )

    if "created_date" in columns:
        updated = User.objects.filter(
            created_date__isnull=True
        ).update(
            created_date=now
        )
        print(
            f"created_date repaired: {updated} existing rows"
        )

    if "updated_date" in columns:
        updated = User.objects.filter(
            updated_date__isnull=True
        ).update(
            updated_date=now
        )
        print(
            f"updated_date repaired: {updated} existing rows"
        )

    # --------------------------------------------------------
    # Convert repaired columns back to the actual model fields
    # --------------------------------------------------------

    with connection.schema_editor() as schema_editor:

        for field_name in fields_to_repair:

            if field_name not in columns:
                continue

            original_field = User._meta.get_field(field_name)

            repair_field = original_field.clone()
            repair_field.null = True
            repair_field.default = None

            # Only alter if database currently has nullable version.
            try:
                schema_editor.alter_field(
                    User,
                    repair_field,
                    original_field,
                    strict=False,
                )
                print(
                    f"Finalized accounts_user.{field_name}"
                )
            except Exception as exc:
                print(
                    f"WARNING: Could not finalize "
                    f"{field_name}: {exc}"
                )

    print("")
    print("ACCOUNTS SCHEMA REPAIR COMPLETED.")


# ============================================================
# COUPONS
# ============================================================

print("")
print("---- COUPONS ----")

with connection.cursor() as cursor:
    tables = connection.introspection.table_names()

if "coupons_couponusage" not in tables:
    print("WARNING: coupons_couponusage missing.")

    from coupons.models import CouponUsage

    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(CouponUsage)

    print("SUCCESS: coupons_couponusage created.")
else:
    print("OK: coupons_couponusage already exists.")


# ============================================================
# CUSTOMIZATION
# ============================================================

print("")
print("---- CUSTOMIZATION ----")

with connection.cursor() as cursor:
    tables = connection.introspection.table_names()

if "customization_customization" in tables:

    with connection.cursor() as cursor:
        customization_columns = {
            col.name
            for col in connection.introspection.get_table_description(
                cursor,
                "customization_customization"
            )
        }

    print("Existing customization columns:")
    for column in sorted(customization_columns):
        print(" -", column)

    from customization.models import Customization

    # Current model fields that may be missing from the
    # already-existing Render table.
    customization_repairs = [
        "via_whatsapp",
        "whatsapp_message",
    ]

    for field_name in customization_repairs:

        if field_name in customization_columns:
            print(
                f"OK: customization_customization.{field_name}"
            )
            continue

        print(
            f"REPAIRING: customization_customization.{field_name}"
        )

        original_field = Customization._meta.get_field(
            field_name
        )

        repair_field = original_field.clone()

        repair_field.null = True
        repair_field.default = None

        with connection.schema_editor() as schema_editor:
            schema_editor.add_field(
                Customization,
                repair_field
            )

        print(
            f"Created customization column: {field_name}"
        )

else:
    print(
        "customization_customization does not exist. "
        "Django migrations will create it."
    )


# ============================================================
# CUSTOMIZATION IMAGE
# ============================================================

if "customization_customizationimage" in tables:
    print(
        "OK: customization_customizationimage already exists."
    )
else:
    print(
        "WARNING: customization_customizationimage missing."
    )

    try:
        from customization.models import CustomizationImage

        with connection.schema_editor() as schema_editor:
            schema_editor.create_model(CustomizationImage)

        print(
            "SUCCESS: customization_customizationimage created."
        )

    except Exception as exc:
        print(
            "WARNING: Could not create CustomizationImage:"
        )
        print(exc)


# ============================================================
# FINAL SCHEMA REPORT
# ============================================================

print("")
print("======================================")
print(" FINAL DATABASE SCHEMA CHECK")
print("======================================")

with connection.cursor() as cursor:
    tables = connection.introspection.table_names()

for table in [
    "accounts_user",
    "coupons_coupon",
    "coupons_couponusage",
    "customization_customization",
    "customization_customizationimage",
]:

    exists = table in tables

    print(
        f"{table}: "
        f"{'EXISTS' if exists else 'MISSING'}"
    )

    if exists:
        with connection.cursor() as cursor:
            cols = [
                col.name
                for col in connection.introspection.get_table_description(
                    cursor,
                    table
                )
            ]

        print("  columns:")
        for col in cols:
            print("   -", col)

print("")
print("DATABASE SCHEMA REPAIR FINISHED.")

PY

echo "======================================"
echo " MIGRATION STATUS BEFORE MIGRATE"
echo "======================================"

python manage.py showmigrations accounts
python manage.py showmigrations coupons
python manage.py showmigrations customization

echo "======================================"
echo " RUNNING DJANGO MIGRATIONS"
echo "======================================"

python manage.py migrate --noinput

echo "======================================"
echo " FINAL DJANGO CHECK"
echo "======================================"

python manage.py check

echo "======================================"
echo " DIGITAL GALLERIA BUILD SUCCESSFUL"
echo "======================================"
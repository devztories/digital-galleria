#!/usr/bin/env bash

set -o errexit

echo "======================================"
echo " DIGITAL GALLERIA - RENDER BUILD"
echo "======================================"

# ============================================================
# 1. INSTALL DEPENDENCIES
# ============================================================

echo ""
echo "======================================"
echo " INSTALLING DEPENDENCIES"
echo "======================================"

pip install -r requirements.txt


# ============================================================
# 2. DJANGO CHECK
# ============================================================

echo ""
echo "======================================"
echo " CHECKING DJANGO"
echo "======================================"

python manage.py check


# ============================================================
# 3. COLLECT STATIC FILES
# ============================================================

echo ""
echo "======================================"
echo " COLLECTING STATIC FILES"
echo "======================================"

python manage.py collectstatic --no-input


# ============================================================
# 4. DATABASE SCHEMA REPAIR
# ============================================================

echo ""
echo "======================================"
echo " DATABASE SCHEMA REPAIR"
echo "======================================"

python manage.py shell <<'PY'

from django.db import connection
from django.db.migrations.loader import MigrationLoader
from django.db.migrations.recorder import MigrationRecorder


# ============================================================
# HELPERS
# ============================================================

def get_tables():
    return connection.introspection.table_names()


def get_columns(table_name):
    with connection.cursor() as cursor:
        return [
            column.name
            for column in connection.introspection.get_table_description(
                cursor,
                table_name
            )
        ]


def migration_exists(app, name):
    return MigrationRecorder(connection).migration_qs.filter(
        app=app,
        name=name
    ).exists()


def migration_available(app, name):
    loader = MigrationLoader(
        connection,
        ignore_no_migrations=True
    )

    return (app, name) in loader.disk_migrations


def mark_migration(app, name):

    if migration_exists(app, name):

        print(
            f"OK: {app}.{name} already recorded."
        )

        return

    print(
        f"Recording {app}.{name}..."
    )

    MigrationRecorder(connection).record_applied(
        app,
        name
    )

    print(
        f"SUCCESS: {app}.{name} recorded."
    )


def add_column_if_missing(
    table_name,
    column_name,
    sql
):

    tables = get_tables()

    if table_name not in tables:

        print(
            f"ERROR: {table_name} does not exist."
        )

        raise SystemExit(1)

    columns = get_columns(
        table_name
    )

    if column_name in columns:

        print(
            f"OK: {table_name}.{column_name} already exists."
        )

        return

    print(
        f"Adding {table_name}.{column_name}..."
    )

    with connection.cursor() as cursor:

        cursor.execute(sql)

    print(
        f"SUCCESS: {table_name}.{column_name} added."
    )


# ============================================================
# START
# ============================================================

print("")
print("======================================")
print(" DATABASE SCHEMA CHECK")
print("======================================")


# ============================================================
# 5. COUPONS
# ============================================================

print("")
print("======================================")
print(" COUPONS")
print("======================================")


coupon_table = "coupons_coupon"
coupon_usage_table = "coupons_couponusage"

tables = get_tables()


# ------------------------------------------------------------
# Coupon table
# ------------------------------------------------------------

if coupon_table not in tables:

    print(
        "WARNING: coupons_coupon is missing."
    )

    loader = MigrationLoader(
        connection,
        ignore_no_migrations=True
    )

    state = loader.project_state(
        [
            (
                "coupons",
                "0001_initial"
            )
        ]
    )

    Coupon = state.apps.get_model(
        "coupons",
        "Coupon"
    )

    CouponUsage = state.apps.get_model(
        "coupons",
        "CouponUsage"
    )

    with connection.schema_editor() as schema_editor:

        schema_editor.create_model(
            Coupon
        )

        schema_editor.create_model(
            CouponUsage
        )

    print(
        "SUCCESS: coupons base tables created."
    )

else:

    print(
        "OK: coupons_coupon exists."
    )


# ------------------------------------------------------------
# CouponUsage table
# ------------------------------------------------------------

tables = get_tables()

if coupon_usage_table not in tables:

    print(
        "WARNING: coupons_couponusage is missing."
    )

    loader = MigrationLoader(
        connection,
        ignore_no_migrations=True
    )

    state = loader.project_state(
        [
            (
                "coupons",
                "0001_initial"
            )
        ]
    )

    CouponUsage = state.apps.get_model(
        "coupons",
        "CouponUsage"
    )

    with connection.schema_editor() as schema_editor:

        schema_editor.create_model(
            CouponUsage
        )

    print(
        "SUCCESS: coupons_couponusage created."
    )

else:

    print(
        "OK: coupons_couponusage exists."
    )


# ------------------------------------------------------------
# CouponUsage order_id
# ------------------------------------------------------------

add_column_if_missing(
    "coupons_couponusage",
    "order_id",
    """
    ALTER TABLE coupons_couponusage
    ADD COLUMN order_id BIGINT NULL
    """
)


# ------------------------------------------------------------
# CouponUsage user_id
# ------------------------------------------------------------

add_column_if_missing(
    "coupons_couponusage",
    "user_id",
    """
    ALTER TABLE coupons_couponusage
    ADD COLUMN user_id BIGINT NULL
    """
)


# ------------------------------------------------------------
# Coupon migration state
# ------------------------------------------------------------

if migration_available(
    "coupons",
    "0001_initial"
):

    mark_migration(
        "coupons",
        "0001_initial"
    )


if migration_available(
    "coupons",
    "0002_couponusage_order_couponusage_user"
):

    columns = get_columns(
        coupon_usage_table
    )

    if (
        "order_id" in columns
        and
        "user_id" in columns
    ):

        mark_migration(
            "coupons",
            "0002_couponusage_order_couponusage_user"
        )

    else:

        print(
            "ERROR: CouponUsage schema incomplete."
        )

        raise SystemExit(1)


# ============================================================
# 6. CUSTOMIZATION
# ============================================================

print("")
print("======================================")
print(" CUSTOMIZATION")
print("======================================")


customization_table = (
    "customization_customization"
)

customization_image_table = (
    "customization_customizationimage"
)

tables = get_tables()


# ------------------------------------------------------------
# Main customization table
# ------------------------------------------------------------

if customization_table not in tables:

    print(
        "ERROR: customization_customization does not exist."
    )

    raise SystemExit(1)

else:

    print(
        "OK: customization_customization exists."
    )


# ------------------------------------------------------------
# via_whatsapp
# ------------------------------------------------------------

add_column_if_missing(
    customization_table,
    "via_whatsapp",
    """
    ALTER TABLE customization_customization
    ADD COLUMN via_whatsapp BOOLEAN
    NOT NULL DEFAULT FALSE
    """
)


# ------------------------------------------------------------
# whatsapp_message
# ------------------------------------------------------------

add_column_if_missing(
    customization_table,
    "whatsapp_message",
    """
    ALTER TABLE customization_customization
    ADD COLUMN whatsapp_message TEXT
    NOT NULL DEFAULT ''
    """
)


# ------------------------------------------------------------
# CustomizationImage
# ------------------------------------------------------------

tables = get_tables()

if customization_image_table in tables:

    print(
        "OK: customization_customizationimage exists."
    )

else:

    print(
        "WARNING: customization_customizationimage is missing."
    )

    loader = MigrationLoader(
        connection,
        ignore_no_migrations=True
    )

    state = loader.project_state(
        [
            (
                "customization",
                "0002_customization_via_whatsapp_and_more"
            )
        ]
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
# Verify customization
# ------------------------------------------------------------

tables = get_tables()

columns = get_columns(
    customization_table
)

print("")
print("CUSTOMIZATION COLUMNS:")

for column in columns:

    print(
        " -",
        column
    )


if (
    "via_whatsapp" not in columns
    or
    "whatsapp_message" not in columns
    or
    customization_image_table not in tables
):

    print(
        "ERROR: Customization schema incomplete."
    )

    raise SystemExit(1)


print(
    "SUCCESS: Customization schema ready."
)


# ------------------------------------------------------------
# Customization migration state
# ------------------------------------------------------------

if migration_available(
    "customization",
    "0001_initial"
):

    mark_migration(
        "customization",
        "0001_initial"
    )


if migration_available(
    "customization",
    "0002_customization_via_whatsapp_and_more"
):

    mark_migration(
        "customization",
        "0002_customization_via_whatsapp_and_more"
    )


# ============================================================
# 7. ACCOUNTS
# ============================================================

print("")
print("======================================")
print(" ACCOUNTS")
print("======================================")


accounts_table = "accounts_user"

tables = get_tables()


# ------------------------------------------------------------
# Accounts table
# ------------------------------------------------------------

if accounts_table not in tables:

    print(
        "ERROR: accounts_user does not exist."
    )

    raise SystemExit(1)

else:

    print(
        "OK: accounts_user exists."
    )


# ------------------------------------------------------------
# Show current columns
# ------------------------------------------------------------

columns = get_columns(
    accounts_table
)

print("")
print("CURRENT ACCOUNTS COLUMNS:")

for column in columns:

    print(
        " -",
        column
    )


# ============================================================
# theme_preference
# ============================================================

add_column_if_missing(
    accounts_table,
    "theme_preference",
    """
    ALTER TABLE accounts_user
    ADD COLUMN theme_preference VARCHAR(10)
    NOT NULL DEFAULT 'system'
    """
)


# ============================================================
# preferred_vehicle
# ============================================================

add_column_if_missing(
    accounts_table,
    "preferred_vehicle",
    """
    ALTER TABLE accounts_user
    ADD COLUMN preferred_vehicle VARCHAR(10)
    NOT NULL DEFAULT 'bike'
    """
)


# ============================================================
# created_date
#
# Render DB currently has created_at.
# Django model expects created_date.
#
# Preserve existing data by renaming.
# ============================================================

columns = get_columns(
    accounts_table
)

if "created_date" in columns:

    print(
        "OK: created_date already exists."
    )

elif "created_at" in columns:

    print("")
    print(
        "created_date missing."
    )

    print(
        "Existing created_at found."
    )

    print(
        "Renaming created_at -> created_date..."
    )

    with connection.cursor() as cursor:

        cursor.execute(
            """
            ALTER TABLE accounts_user
            RENAME COLUMN created_at TO created_date
            """
        )

    print(
        "SUCCESS: created_at renamed to created_date."
    )

else:

    print("")
    print(
        "created_date and created_at are both missing."
    )

    print(
        "Creating created_date..."
    )

    with connection.cursor() as cursor:

        cursor.execute(
            """
            ALTER TABLE accounts_user
            ADD COLUMN created_date TIMESTAMP NULL
            """
        )

    print(
        "SUCCESS: created_date created."
    )


# ============================================================
# updated_date
# ============================================================

columns = get_columns(
    accounts_table
)

if "updated_date" in columns:

    print(
        "OK: updated_date already exists."
    )

elif "updated_at" in columns:

    print("")
    print(
        "updated_date missing."
    )

    print(
        "Existing updated_at found."
    )

    print(
        "Renaming updated_at -> updated_date..."
    )

    with connection.cursor() as cursor:

        cursor.execute(
            """
            ALTER TABLE accounts_user
            RENAME COLUMN updated_at TO updated_date
            """
        )

    print(
        "SUCCESS: updated_at renamed to updated_date."
    )

else:

    print("")
    print(
        "updated_date is missing."
    )

    print(
        "Creating updated_date..."
    )

    with connection.cursor() as cursor:

        cursor.execute(
            """
            ALTER TABLE accounts_user
            ADD COLUMN updated_date TIMESTAMP NULL
            """
        )

    print(
        "SUCCESS: updated_date created."
    )


# ============================================================
# FINAL ACCOUNTS CHECK
# ============================================================

columns = get_columns(
    accounts_table
)

print("")
print("======================================")
print(" FINAL ACCOUNTS SCHEMA")
print("======================================")


required_account_columns = [
    "theme_preference",
    "preferred_vehicle",
    "created_date",
    "updated_date",
]


accounts_ready = True


for column in required_account_columns:

    exists = column in columns

    print(
        f"{column}: {exists}"
    )

    if not exists:

        accounts_ready = False


if not accounts_ready:

    print("")
    print(
        "ERROR: Accounts schema is incomplete."
    )

    raise SystemExit(1)


print("")
print(
    "SUCCESS: Accounts schema is ready."
)


# ============================================================
# Accounts migration state
# ============================================================

if migration_available(
    "accounts",
    "0001_initial"
):

    mark_migration(
        "accounts",
        "0001_initial"
    )


# Theme migration may have different names
# depending on which migration file exists.

possible_accounts_migrations = [
    "0002_theme_system",
    "0002_alter_user_theme_preference",
]


for migration_name in possible_accounts_migrations:

    if migration_available(
        "accounts",
        migration_name
    ):

        print(
            f"Found {migration_name}"
        )

        # Since theme_preference has already been
        # manually repaired above, record the migration
        # instead of trying to ALTER the existing column.

        if "theme_preference" in get_columns(
            accounts_table
        ):

            mark_migration(
                "accounts",
                migration_name
            )


# ============================================================
# 8. FINAL DATABASE VALIDATION
# ============================================================

print("")
print("======================================")
print(" FINAL DATABASE VALIDATION")
print("======================================")


tables = get_tables()


# ------------------------------------------------------------
# Coupons
# ------------------------------------------------------------

print("")
print("---- COUPONS ----")

print(
    "coupons_coupon:",
    "coupons_coupon" in tables
)

print(
    "coupons_couponusage:",
    "coupons_couponusage" in tables
)


if "coupons_couponusage" in tables:

    columns = get_columns(
        "coupons_couponusage"
    )

    print(
        "order_id:",
        "order_id" in columns
    )

    print(
        "user_id:",
        "user_id" in columns
    )


# ------------------------------------------------------------
# Customization
# ------------------------------------------------------------

print("")
print("---- CUSTOMIZATION ----")

print(
    "customization_customization:",
    "customization_customization" in tables
)

print(
    "customization_customizationimage:",
    "customization_customizationimage" in tables
)


if "customization_customization" in tables:

    columns = get_columns(
        "customization_customization"
    )

    print(
        "via_whatsapp:",
        "via_whatsapp" in columns
    )

    print(
        "whatsapp_message:",
        "whatsapp_message" in columns
    )


# ------------------------------------------------------------
# Accounts
# ------------------------------------------------------------

print("")
print("---- ACCOUNTS ----")

print(
    "accounts_user:",
    "accounts_user" in tables
)


if "accounts_user" in tables:

    columns = get_columns(
        "accounts_user"
    )

    print(
        "theme_preference:",
        "theme_preference" in columns
    )

    print(
        "preferred_vehicle:",
        "preferred_vehicle" in columns
    )

    print(
        "created_date:",
        "created_date" in columns
    )

    print(
        "updated_date:",
        "updated_date" in columns
    )


# ============================================================
# FINAL HARD CHECK
# ============================================================

required_tables = [
    "coupons_coupon",
    "coupons_couponusage",
    "customization_customization",
    "customization_customizationimage",
    "accounts_user",
]


missing_tables = [
    table
    for table in required_tables
    if table not in tables
]


if missing_tables:

    print("")
    print(
        "ERROR: Required tables are missing:"
    )

    for table in missing_tables:

        print(
            " -",
            table
        )

    raise SystemExit(1)


accounts_columns = get_columns(
    accounts_table
)

required_columns = [
    "theme_preference",
    "preferred_vehicle",
    "created_date",
    "updated_date",
]


missing_columns = [
    column
    for column in required_columns
    if column not in accounts_columns
]


if missing_columns:

    print("")
    print(
        "ERROR: Required accounts columns are missing:"
    )

    for column in missing_columns:

        print(
            " -",
            column
        )

    raise SystemExit(1)


print("")
print(
    "======================================"
)

print(
    " DATABASE SCHEMA REPAIR SUCCESSFUL"
)

print(
    "======================================"
)


PY


# ============================================================
# 9. MIGRATION STATUS
# ============================================================

echo ""
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


# ============================================================
# 10. RUN MIGRATIONS
# ============================================================

echo ""
echo "======================================"
echo " RUNNING DATABASE MIGRATIONS"
echo "======================================"


python manage.py migrate --noinput


# ============================================================
# 11. FINAL DJANGO CHECK
# ============================================================

echo ""
echo "======================================"
echo " FINAL DJANGO CHECK"
echo "======================================"


python manage.py check


# ============================================================
# 12. FINAL MIGRATION STATUS
# ============================================================

echo ""
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


# ============================================================
# 13. SUCCESS
# ============================================================

echo ""
echo "======================================"
echo " DIGITAL GALLERIA BUILD SUCCESSFUL"
echo "======================================"
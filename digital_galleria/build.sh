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
                table_name,
            )
        ]


def migration_recorded(app, name):
    return MigrationRecorder(connection).migration_qs.filter(
        app=app,
        name=name,
    ).exists()


def migration_available(app, name):
    loader = MigrationLoader(
        connection,
        ignore_no_migrations=True,
    )

    return (app, name) in loader.disk_migrations


def mark_migration(app, name):
    if not migration_recorded(app, name):

        MigrationRecorder(connection).record_applied(
            app,
            name,
        )

        print(
            f"SUCCESS: recorded {app}.{name}"
        )

    else:

        print(
            f"OK: {app}.{name} already recorded"
        )


def add_column_if_missing(
    table_name,
    column_name,
    sql,
):
    tables = get_tables()

    if table_name not in tables:

        print(
            f"ERROR: table {table_name} does not exist."
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
        f"WARNING: {table_name}.{column_name} is missing."
    )

    print(
        f"Creating {table_name}.{column_name}..."
    )

    with connection.cursor() as cursor:
        cursor.execute(sql)

    print(
        f"SUCCESS: {table_name}.{column_name} created."
    )


# ============================================================
# START
# ============================================================

print("")
print("======================================")
print(" DATABASE SCHEMA STATUS")
print("======================================")


# ============================================================
# 5. COUPONS
# ============================================================

print("")
print("======================================")
print(" COUPONS")
print("======================================")

tables = get_tables()

coupon_table = "coupons_coupon"
coupon_usage_table = "coupons_couponusage"


# ------------------------------------------------------------
# Coupon main table
# ------------------------------------------------------------

if coupon_table not in tables:

    print(
        "WARNING: coupons_coupon is missing."
    )

    print(
        "Creating coupons tables from coupons.0001_initial..."
    )

    loader = MigrationLoader(
        connection,
        ignore_no_migrations=True,
    )

    state = loader.project_state(
        [("coupons", "0001_initial")]
    )

    Coupon = state.apps.get_model(
        "coupons",
        "Coupon",
    )

    CouponUsage = state.apps.get_model(
        "coupons",
        "CouponUsage",
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
        "OK: coupons_coupon already exists."
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

        schema_editor.create_model(
            CouponUsage
        )

    print(
        "SUCCESS: coupons_couponusage created."
    )

else:

    print(
        "OK: coupons_couponusage already exists."
    )


# ------------------------------------------------------------
# CouponUsage columns required by 0002
# ------------------------------------------------------------

add_column_if_missing(
    "coupons_couponusage",
    "order_id",
    """
    ALTER TABLE coupons_couponusage
    ADD COLUMN order_id BIGINT NULL
    """,
)

add_column_if_missing(
    "coupons_couponusage",
    "user_id",
    """
    ALTER TABLE coupons_couponusage
    ADD COLUMN user_id BIGINT NULL
    """,
)


# ------------------------------------------------------------
# Record coupon migrations only when schema is ready
# ------------------------------------------------------------

tables = get_tables()

coupon_ready = (
    "coupons_coupon" in tables
    and
    "coupons_couponusage" in tables
    and
    "order_id" in get_columns(
        "coupons_couponusage"
    )
    and
    "user_id" in get_columns(
        "coupons_couponusage"
    )
)


if coupon_ready:

    if migration_available(
        "coupons",
        "0001_initial",
    ):

        mark_migration(
            "coupons",
            "0001_initial",
        )

    if migration_available(
        "coupons",
        "0002_couponusage_order_couponusage_user",
    ):

        mark_migration(
            "coupons",
            "0002_couponusage_order_couponusage_user",
        )

else:

    print(
        "ERROR: Coupon schema is incomplete."
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
        "ERROR: customization_customization table is missing."
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
    """,
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
    """,
)


# ------------------------------------------------------------
# CustomizationImage table
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
        ignore_no_migrations=True,
    )

    state = loader.project_state(
        [
            (
                "customization",
                "0002_customization_via_whatsapp_and_more",
            )
        ]
    )

    CustomizationImage = state.apps.get_model(
        "customization",
        "CustomizationImage",
    )

    with connection.schema_editor() as schema_editor:

        schema_editor.create_model(
            CustomizationImage
        )

    print(
        "SUCCESS: CustomizationImage created."
    )


# ------------------------------------------------------------
# Verify customization schema
# ------------------------------------------------------------

tables = get_tables()

customization_columns = get_columns(
    customization_table
)

customization_ready = (
    "via_whatsapp" in customization_columns
    and
    "whatsapp_message" in customization_columns
    and
    customization_image_table in tables
)


if not customization_ready:

    print(
        "ERROR: Customization schema is incomplete."
    )

    print(
        "Columns:",
        customization_columns,
    )

    raise SystemExit(1)


print(
    "SUCCESS: Customization schema is ready."
)


# ------------------------------------------------------------
# Record customization migrations
# ------------------------------------------------------------

if migration_available(
    "customization",
    "0001_initial",
):

    mark_migration(
        "customization",
        "0001_initial",
    )


if migration_available(
    "customization",
    "0002_customization_via_whatsapp_and_more",
):

    mark_migration(
        "customization",
        "0002_customization_via_whatsapp_and_more",
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
        "ERROR: accounts_user table is missing."
    )

    raise SystemExit(1)

else:

    print(
        "OK: accounts_user exists."
    )


# ------------------------------------------------------------
# Display current columns
# ------------------------------------------------------------

columns = get_columns(
    accounts_table
)

print(
    "Current accounts columns:"
)

for column in columns:

    print(
        " -",
        column,
    )


# ------------------------------------------------------------
# theme_preference
# ------------------------------------------------------------

add_column_if_missing(
    accounts_table,
    "theme_preference",
    """
    ALTER TABLE accounts_user
    ADD COLUMN theme_preference VARCHAR(10)
    NOT NULL DEFAULT 'system'
    """,
)


# ------------------------------------------------------------
# preferred_vehicle
# ------------------------------------------------------------

add_column_if_missing(
    accounts_table,
    "preferred_vehicle",
    """
    ALTER TABLE accounts_user
    ADD COLUMN preferred_vehicle VARCHAR(10)
    NOT NULL DEFAULT 'bike'
    """,
)


# ------------------------------------------------------------
# Verify accounts schema
# ------------------------------------------------------------

columns = get_columns(
    accounts_table
)

print("")
print(
    "FINAL ACCOUNTS SCHEMA:"
)

print(
    "theme_preference:",
    "theme_preference" in columns,
)

print(
    "preferred_vehicle:",
    "preferred_vehicle" in columns,
)


if "theme_preference" not in columns:

    print(
        "ERROR: theme_preference was not created."
    )

    raise SystemExit(1)


if "preferred_vehicle" not in columns:

    print(
        "ERROR: preferred_vehicle was not created."
    )

    raise SystemExit(1)


print(
    "SUCCESS: accounts schema is ready."
)


# ------------------------------------------------------------
# Record accounts migrations only if they exist
# ------------------------------------------------------------

if migration_available(
    "accounts",
    "0001_initial",
):

    mark_migration(
        "accounts",
        "0001_initial",
    )


# Theme migration may exist in some versions.
# Only record it if the migration file actually exists.

possible_theme_migrations = [
    "0002_theme_system",
    "0002_alter_user_theme_preference",
]


for theme_migration in possible_theme_migrations:

    if migration_available(
        "accounts",
        theme_migration,
    ):

        print(
            f"Found accounts migration: {theme_migration}"
        )

        mark_migration(
            "accounts",
            theme_migration,
        )


# ============================================================
# 8. FINAL DATABASE VERIFICATION
# ============================================================

print("")
print("======================================")
print(" FINAL DATABASE VERIFICATION")
print("======================================")


tables = get_tables()


# ------------------------------------------------------------
# Coupons
# ------------------------------------------------------------

print("")
print("COUPONS:")

print(
    "coupons_coupon:",
    "coupons_coupon" in tables,
)

print(
    "coupons_couponusage:",
    "coupons_couponusage" in tables,
)

if "coupons_couponusage" in tables:

    coupon_usage_columns = get_columns(
        "coupons_couponusage"
    )

    print(
        "order_id:",
        "order_id" in coupon_usage_columns,
    )

    print(
        "user_id:",
        "user_id" in coupon_usage_columns,
    )


# ------------------------------------------------------------
# Customization
# ------------------------------------------------------------

print("")
print("CUSTOMIZATION:")

print(
    "customization_customization:",
    customization_table in tables,
)

print(
    "customization_customizationimage:",
    customization_image_table in tables,
)

if customization_table in tables:

    final_customization_columns = get_columns(
        customization_table
    )

    print(
        "via_whatsapp:",
        "via_whatsapp" in final_customization_columns,
    )

    print(
        "whatsapp_message:",
        "whatsapp_message" in final_customization_columns,
    )


# ------------------------------------------------------------
# Accounts
# ------------------------------------------------------------

print("")
print("ACCOUNTS:")

print(
    "accounts_user:",
    accounts_table in tables,
)

if accounts_table in tables:

    final_account_columns = get_columns(
        accounts_table
    )

    print(
        "theme_preference:",
        "theme_preference" in final_account_columns,
    )

    print(
        "preferred_vehicle:",
        "preferred_vehicle" in final_account_columns,
    )


# ------------------------------------------------------------
# Hard validation
# ------------------------------------------------------------

required_schema = {
    "coupons_coupon": coupon_table in tables,
    "coupons_couponusage": coupon_usage_table in tables,
    "customization_customization": customization_table in tables,
    "customization_customizationimage": customization_image_table in tables,
    "accounts_user": accounts_table in tables,
}


if not all(required_schema.values()):

    print("")
    print(
        "ERROR: One or more required database tables are missing."
    )

    for table, exists in required_schema.items():

        print(
            f"{table}: {exists}"
        )

    raise SystemExit(1)


print("")
print(
    "SUCCESS: Database schema repair completed."
)


PY


# ============================================================
# 9. MIGRATION STATUS BEFORE FINAL MIGRATION
# ============================================================

echo ""
echo "======================================"
echo " MIGRATION STATUS BEFORE FINAL MIGRATE"
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
# 10. RUN REMAINING MIGRATIONS
# ============================================================

echo ""
echo "======================================"
echo " RUNNING REMAINING MIGRATIONS"
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
# 13. BUILD SUCCESS
# ============================================================

echo ""
echo "======================================"
echo " BUILD COMPLETED SUCCESSFULLY"
echo "======================================"
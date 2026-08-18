from django.db import migrations, models


def repair_user_schema(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    connection = schema_editor.connection

    with connection.cursor() as cursor:
        columns = {
            column.name
            for column in connection.introspection.get_table_description(
                cursor,
                User._meta.db_table,
            )
        }

    table = User._meta.db_table

    # preferred_vehicle
    if "preferred_vehicle" not in columns:
        field = User._meta.get_field("preferred_vehicle")
        schema_editor.add_field(User, field)

    # created_date
    if "created_date" not in columns:
        field = User._meta.get_field("created_date")
        schema_editor.add_field(User, field)

    # updated_date
    if "updated_date" not in columns:
        field = User._meta.get_field("updated_date")
        schema_editor.add_field(User, field)


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(
                    repair_user_schema,
                    migrations.RunPython.noop,
                ),
            ],
            state_operations=[],
        ),
    ]
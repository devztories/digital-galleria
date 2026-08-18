from django.db import migrations


def repair_user_schema(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    connection = schema_editor.connection
    table_name = User._meta.db_table

    with connection.cursor() as cursor:
        existing_columns = {
            column.name
            for column in connection.introspection.get_table_description(
                cursor,
                table_name,
            )
        }

    fields_to_repair = [
        "theme_preference",
        "preferred_vehicle",
        "created_date",
        "updated_date",
    ]

    for field_name in fields_to_repair:
        if field_name in existing_columns:
            print(
                f"OK: {table_name}.{field_name} already exists"
            )
            continue

        field = User._meta.get_field(field_name)

        print(
            f"REPAIR: Adding missing column "
            f"{table_name}.{field.column}"
        )

        schema_editor.add_field(
            User,
            field,
        )

        print(
            f"SUCCESS: Added {table_name}.{field.column}"
        )

        existing_columns.add(field.column)


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_repair_missing_columns"),
    ]

    operations = [
        migrations.RunPython(
            repair_user_schema,
            migrations.RunPython.noop,
        ),
    ]
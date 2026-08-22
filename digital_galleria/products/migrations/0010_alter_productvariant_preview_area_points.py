from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0009_migrate_legacy_preview_points'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productvariant',
            name='preview_area_points',
            field=models.JSONField(
                blank=True, default=list,
                help_text=(
                    "DEPRECATED — replaced by the per-image, multi-shape "
                    "products.PreviewArea model. Kept only so old data isn't lost; "
                    "no longer read or written by the customization flow. Use "
                    "Admin → Products → Colour Variants → primary image → "
                    "'Set preview shapes' instead."
                ),
            ),
        ),
    ]

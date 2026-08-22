# Generated manually (multi-shape customization preview areas)

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0007_productvariant_preview_area_points'),
    ]

    operations = [
        migrations.CreateModel(
            name='PreviewArea',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, help_text="Optional label for this shape, e.g. 'Front', 'Left photo'. Shown to admin and, if set, to the customer.", max_length=60)),
                ('points', models.JSONField(help_text='Polygon points (list of [x_percent, y_percent], 0-100) relative to the variant image.')),
                ('display_order', models.PositiveIntegerField(default=0)),
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('variant_image', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='preview_areas', to='products.variantimage')),
            ],
            options={
                'ordering': ['display_order', 'id'],
            },
        ),
    ]

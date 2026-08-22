import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customization', '0003_customizationimage_preview_offset_x_and_more'),
        ('products', '0008_previewarea'),
    ]

    operations = [
        migrations.AddField(
            model_name='customizationimage',
            name='preview_area',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='products.previewarea'),
        ),
    ]

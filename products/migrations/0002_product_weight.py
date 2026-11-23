from django.db import migrations, models
from decimal import Decimal

class Migration(migrations.Migration):
    dependencies = [("products", "0001_initial")]
    operations = [
        migrations.AddField(model_name="product", name="weight", field=models.DecimalField(default=Decimal("0.000"), decimal_places=3, help_text="Product weight in the selected weight unit.", max_digits=8)),
        migrations.AddField(model_name="product", name="weight_unit", field=models.CharField(choices=[("kg", "Kilograms"), ("g", "Grams")], default="kg", max_length=2)),
    ]

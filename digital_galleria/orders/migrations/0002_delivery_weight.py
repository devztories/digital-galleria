from django.db import migrations, models
from decimal import Decimal

class Migration(migrations.Migration):
    dependencies = [("orders", "0001_initial")]
    operations = [
        migrations.AddField(model_name="order", name="total_weight", field=models.DecimalField(default=Decimal("0.000"), decimal_places=3, help_text="Shipment weight snapshot in kg.", max_digits=10)),
        migrations.CreateModel(
            name="DeliveryWeightSlab",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("min_weight", models.DecimalField(decimal_places=3, max_digits=8)),
                ("max_weight", models.DecimalField(blank=True, decimal_places=3, help_text="Leave blank for an open-ended slab.", max_digits=8, null=True)),
                ("charge", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=10)),
                ("is_active", models.BooleanField(default=True)),
                ("priority", models.PositiveIntegerField(default=0, help_text="Lower numbers are evaluated first.")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["priority", "min_weight", "id"]},
        ),
    ]

from django.db import migrations, models
import django.db.models.deletion
from decimal import Decimal


class Migration(migrations.Migration):
    dependencies = [("orders", "0003_order_refund_cancel")]
    operations = [migrations.CreateModel(
        name="DeliveryCountRule",
        fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("min_items", models.PositiveIntegerField()),
            ("max_items", models.PositiveIntegerField(blank=True, null=True)),
            ("charge", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=10)),
            ("is_active", models.BooleanField(default=True)),
            ("priority", models.PositiveIntegerField(default=0)),
        ],
        options={"ordering": ["priority", "min_items", "id"]},
    )]

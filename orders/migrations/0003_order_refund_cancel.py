from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("orders", "0002_delivery_weight")]
    operations = [
        migrations.AddField(model_name="order", name="refund_status", field=models.CharField(choices=[("none", "None"), ("pending", "Pending"), ("completed", "Completed")], default="none", max_length=12)),
        migrations.AddField(model_name="order", name="cancellation_reason", field=models.TextField(blank=True)),
    ]

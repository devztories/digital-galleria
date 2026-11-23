from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("customization", "0001_initial")]
    operations = [
        migrations.AddField(model_name="customization", name="via_whatsapp", field=models.BooleanField(default=False)),
        migrations.AddField(model_name="customization", name="whatsapp_message", field=models.TextField(blank=True)),
        migrations.AlterField(model_name="customization", name="details", field=models.TextField(blank=True, help_text="Optional customer-entered customization details")),
        migrations.CreateModel(
            name="CustomizationImage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("image", models.ImageField(upload_to="customization/reference/")),
                ("display_order", models.PositiveIntegerField(default=0)),
                ("created_date", models.DateTimeField(auto_now_add=True)),
                ("customization", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="images", to="customization.customization")),
            ],
            options={"ordering": ["display_order", "id"]},
        ),
    ]

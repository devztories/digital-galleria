from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0011_alter_previewarea_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="customization_image_mode",
            field=models.CharField(
                choices=[
                    ("both", "Both — customer can upload on the website OR send via WhatsApp"),
                    ("website", "Website only — customer uploads images directly on the website"),
                    ("whatsapp", "WhatsApp only — customer sends images via WhatsApp"),
                ],
                default="both",
                help_text=(
                    "Only applies when 'Customizable' is ticked. Decides how customers send their "
                    "customization images for THIS product: directly to the website (upload), "
                    "via WhatsApp, or both options."
                ),
                max_length=10,
            ),
        ),
    ]

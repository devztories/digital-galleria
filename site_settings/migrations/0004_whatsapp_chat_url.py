from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [("site_settings", "0003_assetscooter")]
    operations = [migrations.AddField(
        model_name="sitesettings", name="whatsapp_chat_url",
        field=models.URLField(blank=True, help_text="Direct WhatsApp chat link used by customer-facing buttons.", max_length=500),
    )]

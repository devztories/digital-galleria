from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("accounts", "0001_initial")]
    operations = [migrations.AlterField(model_name="user", name="theme_preference", field=models.CharField(choices=[("system", "System"), ("dark", "Dark"), ("light", "Light")], default="system", max_length=10))]

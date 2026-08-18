from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("chatbot", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="chatmessage",
            name="attachment",
            field=models.FileField(blank=True, null=True, upload_to="chat/"),
        ),
        migrations.AddField(
            model_name="chatmessage",
            name="attachment_type",
            field=models.CharField(blank=True, choices=[("image", "Image"), ("video", "Video"), ("file", "File")], max_length=10),
        ),
        migrations.AddField(
            model_name="chatmessage",
            name="original_filename",
            field=models.CharField(blank=True, max_length=255),
        ),
    ]

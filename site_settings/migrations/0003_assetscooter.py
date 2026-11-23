from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("site_settings", "0002_design_controls"),
    ]

    operations = [
        migrations.AlterField(
            model_name="assetsetting",
            name="key",
            field=models.CharField(
                max_length=40,
                unique=True,
                choices=[
                    ("delivery_bike", "Delivery Tracking Bike"),
                    ("delivery_scooter", "Delivery Tracking Scooter"),
                    ("delivery_road", "Delivery Road"),
                    ("empty_cart", "Empty Cart Illustration"),
                    ("empty_wishlist", "Empty Wishlist Illustration"),
                    ("empty_search", "No Search Results Illustration"),
                    ("order_success", "Order Success Illustration"),
                    ("refund", "Refund Illustration"),
                    ("error", "Error Illustration"),
                    ("chatbot_avatar", "Chatbot Avatar"),
                    ("brand_circle", "Circular Brand Logo"),
                ],
            ),
        ),
    ]

from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):
    dependencies = [("site_settings", "0001_initial")]

    operations = [
        migrations.AddField(model_name="sitesettings", name="site_title", field=models.CharField(blank=True, default="Digital Galleria", max_length=180)),
        migrations.AddField(model_name="sitesettings", name="footer_logo", field=models.ImageField(blank=True, null=True, upload_to="site/")),
        migrations.AddField(model_name="sitesettings", name="whatsapp_label", field=models.CharField(blank=True, default="Customize via WhatsApp", max_length=80)),
        migrations.AddField(model_name="sitesettings", name="whatsapp_default_message", field=models.TextField(blank=True, default="Hello Digital Galleria, I am sending customization images here.")),
        migrations.AddField(model_name="sitesettings", name="whatsapp_customization_enabled", field=models.BooleanField(default=True)),
        migrations.AddField(model_name="sitesettings", name="whatsapp_include_order_number", field=models.BooleanField(default=True)),
        migrations.AddField(model_name="sitesettings", name="whatsapp_include_product_name", field=models.BooleanField(default=True)),
        migrations.AddField(model_name="sitesettings", name="whatsapp_include_customer_name", field=models.BooleanField(default=False)),
        migrations.AddField(model_name="sitesettings", name="success_sound", field=models.FileField(blank=True, null=True, upload_to="site/sounds/")),
        migrations.AddField(model_name="sitesettings", name="success_sound_enabled", field=models.BooleanField(default=True)),
        migrations.AddField(model_name="sitesettings", name="delivery_mode", field=models.CharField(choices=[("weight", "Weight Based"), ("count", "Product Count Based")], default="weight", max_length=10)),
        migrations.AddField(model_name="sitesettings", name="cancellation_cutoff_status", field=models.CharField(choices=[("verified", "Verified"), ("processing", "Processing"), ("shipped", "Shipped")], default="processing", max_length=12)),
        migrations.AddField(model_name="sitesettings", name="customization_enabled", field=models.BooleanField(default=True)),
        migrations.AddField(model_name="sitesettings", name="customization_max_images", field=models.PositiveIntegerField(default=5, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(20)])),
        migrations.AddField(model_name="sitesettings", name="customization_max_image_size_mb", field=models.PositiveIntegerField(default=5, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(50)])),
        migrations.AddField(model_name="sitesettings", name="customization_allowed_formats", field=models.CharField(blank=True, default="jpg,jpeg,png,webp", max_length=100)),
        migrations.CreateModel(
            name="ThemeSettings",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("background", models.CharField(default="#111214", max_length=20)), ("surface", models.CharField(default="#17181b", max_length=20)),
                ("surface_alt", models.CharField(default="#202125", max_length=20)), ("text", models.CharField(default="#f4f1e9", max_length=20)),
                ("muted_text", models.CharField(default="#a5a5aa", max_length=20)), ("heading", models.CharField(default="#ffffff", max_length=20)),
                ("accent", models.CharField(default="#d9d4c7", max_length=20)), ("button", models.CharField(default="#f4f1e9", max_length=20)),
                ("button_text", models.CharField(default="#111214", max_length=20)), ("button_hover", models.CharField(default="#d7d3c9", max_length=20)),
                ("border", models.CharField(default="#34363a", max_length=20)), ("input_background", models.CharField(default="#1b1c20", max_length=20)),
                ("input_text", models.CharField(default="#f4f1e9", max_length=20)), ("card", models.CharField(default="#17181b", max_length=20)),
                ("header", models.CharField(default="#111214", max_length=20)), ("footer", models.CharField(default="#0d0e10", max_length=20)),
                ("search_background", models.CharField(default="#1b1c20", max_length=20)), ("chatbot_background", models.CharField(default="#17181b", max_length=20)), ("chatbot_surface", models.CharField(default="#202125", max_length=20)), ("chatbot_text", models.CharField(default="#f4f1e9", max_length=20)), ("chatbot_accent", models.CharField(default="#d9d4c7", max_length=20)), ("success", models.CharField(default="#9eb59e", max_length=20)),
                ("danger", models.CharField(default="#c58f8a", max_length=20)), ("admin_background", models.CharField(default="#0f1012", max_length=20)),
                ("admin_surface", models.CharField(default="#17181b", max_length=20)), ("light_background", models.CharField(default="#f5f1e8", max_length=20)),
                ("light_surface", models.CharField(default="#ffffff", max_length=20)), ("light_text", models.CharField(default="#151619", max_length=20)),
                ("light_muted_text", models.CharField(default="#66676b", max_length=20)), ("light_border", models.CharField(default="#d9d5cd", max_length=20)),
                ("default_animation_color_1", models.CharField(default="#111214", max_length=20)), ("default_animation_color_2", models.CharField(default="#6d6e73", max_length=20)),
                ("default_animation_color_3", models.CharField(default="#f4f1e9", max_length=20)), ("animation_enabled", models.BooleanField(default=True)),
                ("animation_speed", models.FloatField(default=1.0, validators=[django.core.validators.MinValueValidator(0.1), django.core.validators.MaxValueValidator(5.0)])),
            ],
        ),
        migrations.CreateModel(
            name="PageTheme",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("page_key", models.CharField(choices=[("home", "Homepage"), ("products_list", "Product Listing"), ("product_detail", "Product Details"), ("category", "Category"), ("search", "Search Results"), ("cart", "Cart"), ("checkout", "Checkout"), ("payment", "UPI Payment"), ("payment_success", "Payment Success"), ("orders", "Orders"), ("order_detail", "Order Details"), ("tracking", "Track Order"), ("cancel", "Cancel / Refund"), ("login", "Login"), ("register", "Register"), ("profile", "Profile"), ("wishlist", "Wishlist"), ("customization", "Customization"), ("empty", "Empty States"), ("error", "Error Pages")], max_length=40, unique=True)),
                *[(name, models.CharField(blank=True, max_length=20)) for name in ["background","surface","text","muted_text","heading","accent","button","button_text","button_hover","border","input_background","input_text","card","header","footer","search_background"]],
            ],
        ),
        migrations.CreateModel(
            name="AssetSetting",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("key", models.CharField(choices=[("delivery_bike", "Delivery Tracking Bike"), ("delivery_road", "Delivery Road"), ("empty_cart", "Empty Cart Illustration"), ("empty_wishlist", "Empty Wishlist Illustration"), ("empty_search", "No Search Results Illustration"), ("order_success", "Order Success Illustration"), ("refund", "Refund Illustration"), ("error", "Error Illustration"), ("chatbot_avatar", "Chatbot Avatar"), ("brand_circle", "Circular Brand Logo")], max_length=40, unique=True)),
                ("asset", models.FileField(blank=True, null=True, upload_to="site/assets/")), ("enabled", models.BooleanField(default=True)), ("alt_text", models.CharField(blank=True, max_length=150)),
            ],
        ),
        migrations.CreateModel(
            name="AnimationSettings",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("key", models.CharField(default="global", max_length=40, unique=True)),
                ("enabled", models.BooleanField(default=True)), ("page_transitions", models.BooleanField(default=True)), ("hover_effects", models.BooleanField(default=True)), ("card_effects", models.BooleanField(default=True)), ("search_effects", models.BooleanField(default=True)), ("modal_effects", models.BooleanField(default=True)), ("success_effects", models.BooleanField(default=True)), ("tracking_effects", models.BooleanField(default=True)), ("cancellation_effects", models.BooleanField(default=True)), ("chatbot_effects", models.BooleanField(default=True)),
                ("duration_ms", models.PositiveIntegerField(default=420, validators=[django.core.validators.MinValueValidator(50), django.core.validators.MaxValueValidator(3000)])), ("intensity", models.FloatField(default=1.0, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(2)])), ("text_flow_enabled", models.BooleanField(default=True)), ("text_flow_duration_ms", models.PositiveIntegerField(default=6500, validators=[django.core.validators.MinValueValidator(1000), django.core.validators.MaxValueValidator(20000)])), ("text_flow_direction", models.CharField(default="90deg", max_length=20)), ("tracking_speed", models.FloatField(default=1.0, validators=[django.core.validators.MinValueValidator(0.1), django.core.validators.MaxValueValidator(5)])), ("bike_size_px", models.PositiveIntegerField(default=44, validators=[django.core.validators.MinValueValidator(24), django.core.validators.MaxValueValidator(100)])),
            ],
        ),
    ]

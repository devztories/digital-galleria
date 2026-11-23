from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=170, unique=True, blank=True)
    image = models.ImageField(upload_to="categories/", blank=True, null=True)
    display_order = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)
    created_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["display_order", "name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def display_image_url(self):
        """Admin-uploaded cover if there is one, otherwise the hard-coded
        static/catalog/<slug>/_cover.* file (see products.static_catalog)."""
        if self.image:
            try:
                return self.image.url
            except ValueError:
                pass
        from products.static_catalog import category_cover
        return category_cover(self.slug)

    def __str__(self):
        return self.name

from django.db import migrations


def forwards(apps, schema_editor):
    """Every ProductVariant that already had a single preview_area_points
    polygon set (the old one-shape-per-colour system) gets that polygon
    carried forward as its first PreviewArea shape, on its primary image —
    so nothing configured by an admin before this upgrade is lost. Admins
    can now add further shapes alongside it, or rename/replace it, from the
    new multi-shape editor.
    """
    ProductVariant = apps.get_model('products', 'ProductVariant')
    VariantImage = apps.get_model('products', 'VariantImage')
    PreviewArea = apps.get_model('products', 'PreviewArea')

    for variant in ProductVariant.objects.exclude(preview_area_points=[]):
        points = variant.preview_area_points
        if not points:
            continue
        primary = VariantImage.objects.filter(variant=variant).order_by('display_order', 'id').first()
        if not primary:
            continue
        PreviewArea.objects.create(variant_image=primary, name='', points=points, display_order=0)


def backwards(apps, schema_editor):
    # No-op: the old single-polygon field is left untouched by forwards(),
    # so there's nothing to restore.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0008_previewarea'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]

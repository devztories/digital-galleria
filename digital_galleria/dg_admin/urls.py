from django.urls import path
from . import views

app_name = "dg_admin"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("search/", views.global_search, name="global_search"),

    path("products/", views.product_list, name="product_list"),
    path("products/add/", views.product_form, name="product_add"),
    path("products/<int:pk>/edit/", views.product_form, name="product_edit"),
    path("products/<int:pk>/delete/", views.product_delete, name="product_delete"),
    path("products/<int:product_id>/variants/add/", views.product_variant_add, name="product_variant_add"),
    path("products/variants/<int:pk>/edit/", views.product_variant_edit, name="product_variant_edit"),
    path("products/variants/<int:pk>/delete/", views.product_variant_delete, name="product_variant_delete"),
    path("products/variants/image/<int:pk>/delete/", views.product_variant_image_delete, name="product_variant_image_delete"),
    path("products/variants/image/<int:pk>/primary/", views.product_variant_image_set_primary, name="product_variant_image_set_primary"),
    path("colours/", views.colour_list, name="colour_list"),
    path("colours/add/", views.colour_add, name="colour_add"),
    path("colours/<int:pk>/edit/", views.colour_edit, name="colour_edit"),
    path("colours/<int:pk>/delete/", views.colour_delete, name="colour_delete"),

    path("categories/", views.category_list, name="category_list"),
    path("categories/add/", views.category_form, name="category_add"),
    path("categories/<int:pk>/edit/", views.category_form, name="category_edit"),
    path("categories/<int:pk>/delete/", views.category_delete, name="category_delete"),

    path("delivery/", views.delivery_list, name="delivery_list"),
    path("delivery/add/", views.delivery_form, name="delivery_add"),
    path("delivery/<int:pk>/edit/", views.delivery_form, name="delivery_edit"),
    path("delivery/<int:pk>/delete/", views.delivery_delete, name="delivery_delete"),
    path("delivery/product/<int:pk>/edit/", views.delivery_edit, name="product_delivery_edit"),
    path("delivery/calculator/", views.delivery_calculator, name="delivery_calculator"),
    path("delivery/count/", views.delivery_count_list, name="delivery_count_list"),
    path("delivery/count/add/", views.delivery_count_form, name="delivery_count_add"),
    path("delivery/count/<int:pk>/edit/", views.delivery_count_form, name="delivery_count_edit"),
    path("delivery/count/<int:pk>/delete/", views.delivery_count_delete, name="delivery_count_delete"),

    path("orders/", views.order_list, name="order_list"),
    path("orders/<str:order_number>/", views.order_detail, name="order_detail"),

    path("payments/", views.payment_list, name="payment_list"),
    path("payments/<int:pk>/review/", views.payment_review, name="payment_review"),

    path("customers/", views.customer_list, name="customer_list"),
    path("customers/<int:pk>/", views.customer_detail, name="customer_detail"),

    path("coupons/", views.coupon_list, name="coupon_list"),
    path("coupons/add/", views.coupon_form, name="coupon_add"),
    path("coupons/<int:pk>/edit/", views.coupon_form, name="coupon_edit"),
    path("coupons/<int:pk>/delete/", views.coupon_delete, name="coupon_delete"),

    path("content/<str:kind>/", views.simple_list, name="simple_list"),
    path("content/<str:kind>/add/", views.simple_form, name="simple_add"),
    path("content/<str:kind>/<int:pk>/edit/", views.simple_form, name="simple_edit"),
    path("content/<str:kind>/<int:pk>/delete/", views.simple_delete, name="simple_delete"),

    path("customization/", views.customization_list, name="customization_list"),

    path("hopy/", views.chat_list, name="chat_list"),
    path("hopy/<int:pk>/", views.chat_detail, name="chat_detail"),

    path("storage/", views.storage_manager, name="storage_manager"),
    path("storage/delete/", views.storage_delete, name="storage_delete"),

    path("reports/", views.reports, name="reports"),
    path("site-settings/", views.site_settings_dashboard, name="site_settings"),
    path("site-settings/legacy/", views.site_settings_view, name="site_settings_legacy"),
    path("site-settings/section/<str:section>/", views.site_settings_section, name="site_settings_section"),
    path("site-settings/page/<str:page_key>/reset/", views.reset_page_theme, name="reset_page_theme"),
    path("site-settings/asset/<str:key>/reset/", views.reset_asset, name="reset_asset"),
    path("products/gallery/<int:pk>/delete/", views.product_gallery_delete, name="product_gallery_delete"),
    path("products/gallery/<int:pk>/primary/", views.product_gallery_set_primary, name="product_gallery_set_primary"),
    path("products/<int:product_id>/gallery/reorder/", views.product_gallery_reorder, name="product_gallery_reorder"),
    path("admin-users/", views.admin_users, name="admin_users"),
    path("admin-users/add/", views.admin_user_form, name="admin_user_add"),
    path("admin-users/<int:pk>/edit/", views.admin_user_form, name="admin_user_edit"),
    path("admin-users/<int:pk>/toggle-active/", views.admin_user_toggle_active, name="admin_user_toggle_active"),
    path("admin-users/<int:pk>/remove-access/", views.admin_user_remove_access, name="admin_user_remove_access"),
    path("audit-log/", views.audit_log, name="audit_log"),
]

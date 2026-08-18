from functools import wraps
from django.contrib.auth.decorators import login_required, user_passes_test

staff_required = user_passes_test(lambda u: u.is_active and u.is_staff, login_url="accounts:login")
superuser_required_test = user_passes_test(lambda u: u.is_active and u.is_superuser, login_url="accounts:login")


def dg_admin_required(view_func):
    @wraps(view_func)
    @login_required
    @staff_required
    def _wrapped(request, *args, **kwargs):
        return view_func(request, *args, **kwargs)
    return _wrapped


def dg_superuser_required(view_func):
    """Stricter than dg_admin_required — only superusers can manage other admin accounts."""
    @wraps(view_func)
    @login_required
    @superuser_required_test
    def _wrapped(request, *args, **kwargs):
        return view_func(request, *args, **kwargs)
    return _wrapped

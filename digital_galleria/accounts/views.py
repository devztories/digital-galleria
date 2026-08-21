from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from site_settings.models import SiteSettings
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404

from .forms import RegisterForm, LoginForm, ProfileForm, PasswordChangeForm, AddressForm
from .models import User, Address
from orders.models import Order


def register_view(request):
    if request.user.is_authenticated:
        return redirect("home")
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                email=form.cleaned_data["email"],
                name=form.cleaned_data["name"],
                password=form.cleaned_data["password"],
                phone=form.cleaned_data.get("phone", ""),
            )
            login(request, user)
            messages.success(request, "Welcome to Digital Galleria!")
            return redirect("home")
    else:
        form = RegisterForm()
    return render(request, "accounts/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("home")
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            login(request, form.cleaned_data["user"])
            messages.success(request, "Logged in successfully.")
            next_url = request.GET.get("next") or "home"
            return redirect(next_url)
    else:
        form = LoginForm()
    return render(request, "accounts/login.html", {"form": form})


@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("home")


@login_required
def profile_view(request):
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated.")
            return redirect("accounts:profile")
    else:
        form = ProfileForm(instance=request.user)
    return render(request, "accounts/profile.html", {"form": form})


@login_required
def my_orders_view(request):
    # Orders still awaiting payment proof aren't confirmed yet, so they don't
    # belong in "My Orders" — they only exist to hold an order_number/stock
    # reservation while the customer is on the payment page.
    orders = Order.objects.filter(user=request.user).exclude(order_status="awaiting_payment").order_by("-created_date")
    cutoff = SiteSettings.load().cancellation_cutoff_status
    stages = ["verified", "processing", "shipped", "delivered"]
    cutoff_index = stages.index(cutoff)
    order_rows = [(order, order.order_status in stages and stages.index(order.order_status) <= cutoff_index) for order in orders]
    return render(request, "accounts/my_orders.html", {"orders": order_rows})


@login_required
def addresses_view(request):
    addresses = request.user.addresses.all().order_by("-is_default", "-created_date")
    if request.method == "POST":
        form = AddressForm(request.POST)
        if form.is_valid():
            addr = form.save(commit=False)
            addr.user = request.user
            if not addresses.exists():
                addr.is_default = True
            addr.save()
            messages.success(request, "Address saved.")
            return redirect("accounts:addresses")
    else:
        form = AddressForm()
    return render(request, "accounts/addresses.html", {"addresses": addresses, "form": form})


@login_required
def delete_address_view(request, pk):
    addr = get_object_or_404(Address, pk=pk, user=request.user)
    addr.delete()
    messages.info(request, "Address removed.")
    return redirect("accounts:addresses")


@login_required
def settings_view(request):
    """Main settings hub. Detail controls live on dedicated subpages."""
    return render(request, "accounts/settings.html")


@login_required
def account_hub_view(request):
    """The single screen that opens when the gear icon is tapped: only a category list, nothing else."""
    return render(request, "accounts/hub.html")


@login_required
def settings_account_view(request):
    return redirect("accounts:profile")


@login_required
def settings_orders_view(request):
    return redirect("accounts:my_orders")


@login_required
def settings_theme_view(request):
    if request.method == "POST":
        theme = request.POST.get("theme")
        if theme in {"system", "dark", "light"}:
            request.user.theme_preference = theme
            request.user.save(update_fields=["theme_preference"])
            messages.success(request, "Theme updated.")
            return redirect("accounts:settings_theme")
    return render(request, "accounts/settings_theme.html")


@login_required
def settings_vehicle_view(request):
    if request.method == "POST":
        vehicle = request.POST.get("vehicle")
        if vehicle in {"bike", "scooter"}:
            request.user.preferred_vehicle = vehicle
            request.user.save(update_fields=["preferred_vehicle"])
            messages.success(request, "Tracking vehicle updated.")
            return redirect("accounts:settings_vehicle")
    return render(request, "accounts/settings_vehicle.html")


@login_required
def settings_customization_view(request):
    return render(request, "accounts/settings_customization.html")


@login_required
def change_password_view(request):
    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            request.user.set_password(form.cleaned_data["new_password"])
            request.user.save()
            login(request, request.user)
            messages.success(request, "Password changed successfully.")
            return redirect("accounts:settings_account")
    else:
        form = PasswordChangeForm(request.user)
    return render(request, "accounts/change_password.html", {"form": form})

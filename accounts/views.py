from django.shortcuts import render, redirect
<<<<<<< HEAD
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import UserProfile


# ==========================
# REGISTER
# ==========================

def register(request):

    if request.method == "POST":

        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        username = request.POST.get("username")
        email = request.POST.get("email")

        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return redirect("register")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect("register")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
            return redirect("register")

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1,
            first_name=first_name,
            last_name=last_name,
        )

        UserProfile.objects.create(user=user)

        login(request, user)

        messages.success(request, "Account created successfully.")

        return redirect("home")

    return render(request, "accounts/register.html")


# ==========================
# LOGIN
# ==========================

def user_login(request):

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            login(request, user)

            messages.success(request, f"Welcome back, {user.first_name or user.username}!")

            return redirect("home")

        messages.error(request, "Invalid username or password.")

    return render(request, "accounts/login.html")


# ==========================
# LOGOUT
# ==========================

def user_logout(request):

    logout(request)

    messages.success(request, "Logged out successfully.")

    return redirect("home")


# ==========================
# PROFILE
# ==========================

@login_required
def profile(request):

    profile, created = UserProfile.objects.get_or_create(
        user=request.user
    )

    if request.method == "POST":

        request.user.first_name = request.POST.get("first_name")
        request.user.last_name = request.POST.get("last_name")
        request.user.email = request.POST.get("email")

        request.user.save()

        profile.phone = request.POST.get("phone")
        profile.address = request.POST.get("address")
        profile.city = request.POST.get("city")
        profile.state = request.POST.get("state")
        profile.pincode = request.POST.get("pincode")

        if request.FILES.get("profile_image"):
            profile.profile_image = request.FILES.get("profile_image")

        profile.save()

        messages.success(request, "Profile updated successfully.")

        return redirect("profile")

    return render(request, "accounts/profile.html", {
        "profile": profile
    })
=======
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.utils.http import url_has_allowed_host_and_scheme
from .forms import RegisterForm, ProfileForm
from .forms import RegisterForm


# =========================================================
# HELPER - SAFE NEXT URL
# =========================================================

def get_safe_next_url(request):

    next_url = (
        request.POST.get("next")
        or request.GET.get("next")
        or ""
    )

    if next_url and url_has_allowed_host_and_scheme(
        url=next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url

    return ""


# =========================================================
# REGISTER
# =========================================================

def register_view(request):

    # If already logged in, go home
    if request.user.is_authenticated:
        return redirect("home")

    next_url = get_safe_next_url(request)

    if request.method == "POST":

        form = RegisterForm(
            request.POST
        )

        if form.is_valid():

            # Create user
            user = form.save()

            # Automatically login new user
            login(
                request,
                user
            )

            # Return to checkout/original page
            if next_url:
                return redirect(next_url)

            # Normal registration
            return redirect("home")

    else:

        form = RegisterForm()

    return render(
        request,
        "accounts/register.html",
        {
            "form": form,
            "next": next_url,
        }
    )


# =========================================================
# LOGIN
# =========================================================

def login_view(request):

    # If already logged in, go home
    if request.user.is_authenticated:
        return redirect("home")

    next_url = get_safe_next_url(request)

    if request.method == "POST":

        form = AuthenticationForm(
            request,
            data=request.POST
        )

        if form.is_valid():

            user = form.get_user()

            # Login user
            login(
                request,
                user
            )

            # Return to original page
            if next_url:
                return redirect(next_url)

            # Normal login
            return redirect("home")

    else:

        form = AuthenticationForm()

    return render(
        request,
        "accounts/login.html",
        {
            "form": form,
            "next": next_url,
        }
    )


# =========================================================
# LOGOUT
# =========================================================

def logout_view(request):

    logout(request)

    return redirect("home")


# =========================================================
# PROFILE
# =========================================================

@login_required(login_url="login")
def profile_view(request):

    if request.method == "POST":

        form = ProfileForm(
            request.POST,
            request.FILES,
            instance=request.user
        )

        if form.is_valid():

            form.save()

            return redirect("profile")

    else:

        form = ProfileForm(
            instance=request.user
        )

    return render(
        request,
        "accounts/profile.html",
        {
            "form": form
        }
    )
@login_required
def profile_view(request):

    if request.method == "POST":

        form = ProfileForm(
            request.POST,
            request.FILES,
            instance=request.user
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Profile updated successfully."
            )

            return redirect("profile")

    else:

        form = ProfileForm(
            instance=request.user
        )


    return render(
        request,
        "accounts/profile.html",
        {
            "form": form
        }
    )
    # =========================================================
# SAVED ADDRESS SYSTEM
# =========================================================

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import (
    render,
    redirect,
    get_object_or_404,
)
from django.views.decorators.http import require_POST

from .models import Address
from .forms import AddressForm


# =========================================================
# VIEW ALL SAVED ADDRESSES
# =========================================================

@login_required(login_url="login")
def saved_addresses(request):

    addresses = Address.objects.filter(
        user=request.user
    )

    return render(
        request,
        "accounts/saved_addresses.html",
        {
            "addresses": addresses,
        }
    )


# =========================================================
# ADD NEW ADDRESS
# =========================================================

@login_required(login_url="login")
def add_address(request):

    if request.method == "POST":

        form = AddressForm(
            request.POST
        )

        if form.is_valid():

            address = form.save(
                commit=False
            )

            # Connect address to logged-in user
            address.user = request.user

            address.save()

            messages.success(
                request,
                "Address saved successfully."
            )

            return redirect(
                "saved_addresses"
            )

    else:

        # ---------------------------------------------
        # Automatically pre-fill name + phone
        # ---------------------------------------------

        initial = {}

        full_name = (
            request.user
            .get_full_name()
            .strip()
        )

        if full_name:

            initial["full_name"] = full_name

        if request.user.phone:

            initial["phone"] = (
                request.user.phone
            )

        form = AddressForm(
            initial=initial
        )


    return render(
        request,
        "accounts/address_form.html",
        {
            "form": form,
            "page_title": "Add Address",
            "submit_text": "Save Address",
        }
    )


# =========================================================
# EDIT SAVED ADDRESS
# =========================================================

@login_required(login_url="login")
def edit_address(
    request,
    address_id
):

    # User can edit only their own address
    address = get_object_or_404(
        Address,
        id=address_id,
        user=request.user,
    )


    if request.method == "POST":

        form = AddressForm(
            request.POST,
            instance=address,
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Address updated successfully."
            )

            return redirect(
                "saved_addresses"
            )

    else:

        form = AddressForm(
            instance=address
        )


    return render(
        request,
        "accounts/address_form.html",
        {
            "form": form,
            "address": address,
            "page_title": "Edit Address",
            "submit_text": "Update Address",
        }
    )


# =========================================================
# SET DEFAULT ADDRESS
# =========================================================

@login_required(login_url="login")
@require_POST
def set_default_address(
    request,
    address_id
):

    address = get_object_or_404(
        Address,
        id=address_id,
        user=request.user,
    )

    address.is_default = True

    address.save()

    messages.success(
        request,
        "Default delivery address updated."
    )

    return redirect(
        "saved_addresses"
    )


# =========================================================
# DELETE ADDRESS
# =========================================================

@login_required(login_url="login")
@require_POST
def delete_address(
    request,
    address_id
):

    address = get_object_or_404(
        Address,
        id=address_id,
        user=request.user,
    )

    # Check whether deleted address was default
    was_default = address.is_default

    address.delete()


    # If default was deleted,
    # automatically make another address default
    if was_default:

        next_address = (
            Address.objects
            .filter(
                user=request.user
            )
            .first()
        )

        if next_address:

            next_address.is_default = True

            next_address.save()


    messages.success(
        request,
        "Address deleted successfully."
    )

    return redirect(
        "saved_addresses"
    )
>>>>>>> d386a61523ce78cb8e24f09895792e16b0693321

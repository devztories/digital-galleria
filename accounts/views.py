from django.shortcuts import render, redirect
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

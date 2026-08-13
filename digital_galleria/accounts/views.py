from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views import View

from .forms import RegistrationForm, ProfileForm, ThemeForm
from orders.models import Order


class GalleriaLoginView(LoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True
    redirect_field_name = 'next'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['next'] = (
            self.request.POST.get(self.redirect_field_name)
            or self.request.GET.get(self.redirect_field_name)
            or ''
        )
        return context

    def form_valid(self, form):
        # Capture the checkout destination BEFORE Django rotates the session.
        next_url = (
            self.request.POST.get(self.redirect_field_name)
            or self.request.GET.get(self.redirect_field_name)
            or ''
        )
        old_session_key = self.request.session.session_key

        # Log the user in.
        login(self.request, form.get_user())

        # Merge the anonymous cart/customization into the authenticated user's cart.
        from cart.models import Cart
        from customization.models import Customization

        user_cart, _ = Cart.objects.get_or_create(
            user=self.request.user,
            defaults={'session_key': self.request.session.session_key},
        )

        if old_session_key:
            guest_cart = (
                Cart.objects.filter(
                    session_key=old_session_key,
                    user__isnull=True
                ).exclude(pk=user_cart.pk).first()
            )
            if guest_cart:
                for item in guest_cart.items.select_related('customization'):
                    item.cart = user_cart
                    item.save(update_fields=['cart'])
                    if item.customization_id:
                        Customization.objects.filter(
                            pk=item.customization_id,
                            user__isnull=True
                        ).update(user=self.request.user)
                guest_cart.delete()

        user_cart.session_key = self.request.session.session_key
        user_cart.save(update_fields=['session_key'])

        # Continue exactly where the customer was sent to login from.
        from django.http import HttpResponseRedirect
        from django.utils.http import url_has_allowed_host_and_scheme

        if next_url and url_has_allowed_host_and_scheme(
            next_url,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure(),
        ):
            return HttpResponseRedirect(next_url)

        return HttpResponseRedirect(self.get_success_url())


def register_view(request):
    if request.user.is_authenticated:
        return redirect('sitecontent:home')

    # Keep the checkout destination and anonymous cart across registration.
    next_url = request.POST.get('next') or request.GET.get('next') or ''
    old_session_key = request.session.session_key

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)

            from cart.models import Cart
            from customization.models import Customization

            user_cart, _ = Cart.objects.get_or_create(
                user=request.user,
                defaults={'session_key': request.session.session_key},
            )

            if old_session_key:
                guest_cart = (
                    Cart.objects.filter(
                        session_key=old_session_key,
                        user__isnull=True
                    ).exclude(pk=user_cart.pk).first()
                )
                if guest_cart:
                    for item in guest_cart.items.select_related('customization'):
                        item.cart = user_cart
                        item.save(update_fields=['cart'])
                        if item.customization_id:
                            Customization.objects.filter(
                                pk=item.customization_id,
                                user__isnull=True
                            ).update(user=request.user)
                    guest_cart.delete()

            user_cart.session_key = request.session.session_key
            user_cart.save(update_fields=['session_key'])

            messages.success(request, 'Welcome to Digital Galleria! Your account has been created.')

            from django.http import HttpResponseRedirect
            from django.utils.http import url_has_allowed_host_and_scheme
            if next_url and url_has_allowed_host_and_scheme(
                next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return HttpResponseRedirect(next_url)

            return HttpResponseRedirect(''.join([request.build_absolute_uri('/')])[:-1] or '/')
    else:
        form = RegistrationForm()

    return render(request, 'accounts/register.html', {
        'form': form,
        'next': next_url,
    })


def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('sitecontent:home')


@login_required
def settings_view(request):
    return render(request, 'accounts/settings.html')


@login_required
def profile_view(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('accounts:profile')
    else:
        form = ProfileForm(instance=request.user)
    return render(request, 'accounts/profile.html', {'form': form})


@login_required
def theme_view(request):
    if request.method == 'POST':
        theme = request.POST.get('theme')
        if theme in ('dark', 'light'):
            request.user.theme = theme
            request.user._theme_explicitly_set = True
            request.user.save(update_fields=['theme'])
            messages.success(request, 'Theme updated.')
        return redirect('accounts:settings')
    return render(request, 'accounts/theme.html')


@login_required
def my_orders_view(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'accounts/orders.html', {'orders': orders})

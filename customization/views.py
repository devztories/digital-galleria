<<<<<<< HEAD
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from store.models import Product
from .forms import ProductCustomizationForm


@login_required
def customize_product(request, product_id):

    product = get_object_or_404(
        Product,
        id=product_id
    )

    if request.method == "POST":

        form = ProductCustomizationForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            customization = form.save(commit=False)

            customization.product = product

            customization.customer = request.user

            customization.save()

            # =========================
            # Add product to cart
            # =========================

            cart = request.session.get("cart", {})

            product_id = str(product.id)

            if product_id in cart:
                cart[product_id] += 1
            else:
                cart[product_id] = 1

            request.session["cart"] = cart

            # Save customization id
            request.session["customization_id"] = customization.id

            return redirect("cart")

    else:

        form = ProductCustomizationForm()

    return render(
        request,
        "customization/customize_product.html",
        {
            "product": product,
            "form": form,
        }
    )
=======
from django.shortcuts import render

# Create your views here.
>>>>>>> d386a61523ce78cb8e24f09895792e16b0693321

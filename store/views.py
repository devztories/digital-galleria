from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.contrib.auth.decorators import login_required

from .models import (
    Product,
    Category,
    Review
)


def home(request):

    categories = Category.objects.all()

    products = Product.objects.filter(
        available=True
    )

    featured_products = Product.objects.filter(
        available=True,
        featured=True
    )

    query = request.GET.get("q")

    if query:

        products = products.filter(

            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query)

        )

    category = request.GET.get("category")

    if category:

        products = products.filter(
            category_id=category
        )

    sort = request.GET.get("sort")

    if sort == "low":

        products = products.order_by("price")

    elif sort == "high":

        products = products.order_by("-price")

    elif sort == "new":

        products = products.order_by("-created_at")

    stock = request.GET.get("stock")

    if stock:

        products = products.filter(
            stock__gt=0
        )

    context = {

        "products": products,

        "featured_products": featured_products,

        "categories": categories,

    }

    return render(
        request,
        "store/home.html",
        context
    )


def category_products(request, category_id):

    category = get_object_or_404(
        Category,
        id=category_id
    )

    products = Product.objects.filter(
        category=category,
        available=True
    )

    return render(
        request,
        "store/category.html",
        {

            "category": category,

            "products": products

        }
    )


from django.shortcuts import render, get_object_or_404
from .models import Product, Review


def product_detail(request, product_id):

    product = get_object_or_404(
        Product,
        id=product_id,
        available=True
    )

    related_products = (
        Product.objects.filter(
            category=product.category,
            available=True
        )
        .exclude(id=product.id)
        [:4]
    )

    reviews = (
        Review.objects.filter(product=product)
        .select_related("user")
        .order_by("-id")
    )

    context = {
        "product": product,
        "related_products": related_products,
        "reviews": reviews,
    }

    return render(
        request,
        "store/product_detail.html",
        context
    )

@login_required
def add_review(request, product_id):

    product = get_object_or_404(
        Product,
        id=product_id
    )

    if request.method == "POST":

        rating = request.POST.get("rating")

        comment = request.POST.get("comment")

        Review.objects.create(

            product=product,

            user=request.user,

            rating=rating,

            comment=comment

        )

    return redirect(
        "product_detail",
        product_id=product.id
    )
from .models import Product, Category


def shop(request):
    products = Product.objects.filter(available=True)
    categories = Category.objects.all()

    return render(request, "store/shop.html", {
        "products": products,
        "categories": categories,
    })


def about(request):
    return render(request, "store/about.html")


def contact(request):
    return render(request, "store/contact.html")
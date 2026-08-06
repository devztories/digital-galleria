from django.shortcuts import render, redirect, get_object_or_404
from store.models import Product

def wishlist(request):

    wishlist = request.session.get("wishlist", {})

    wishlist_items = []

    for product_id in wishlist:

        product = get_object_or_404(Product,id=product_id)

        wishlist_items.append({

            "product":product

        })

    return render(

        request,

        "wishlist/wishlist.html",

        {

            "wishlist_items":wishlist_items

        }

    )


def add_wishlist(request,product_id):

    wishlist=request.session.get("wishlist",{})

    wishlist[str(product_id)]=1

    request.session["wishlist"]=wishlist

    return redirect("wishlist")


def remove_wishlist(request,product_id):

    wishlist=request.session.get("wishlist",{})

    wishlist.pop(str(product_id),None)

    request.session["wishlist"]=wishlist

    return redirect("wishlist")
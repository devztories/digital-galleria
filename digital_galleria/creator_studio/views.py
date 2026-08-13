from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum
from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta

from accounts.models import User
from products.models import Product
from categories.models import Category
from orders.models import Order
from customization.models import Customization
from payments.models import PaymentProof
from coupons.models import Coupon
from offers.models import Offer
from advertisements.models import Advertisement
from sitecontent.models import Banner, StorySlide, SiteSettings
from chatbot.models import ChatConversation, ChatMessage

@staff_member_required
def home(request):
    now = timezone.now()
    today = now.date()
    orders = Order.objects.all()
    sales = orders.filter(created_at__date=today).aggregate(v=Sum('grand_total'))['v'] or 0
    context = {
        'users': User.objects.count(),
        'products': Product.objects.count(),
        'categories': Category.objects.count(),
        'orders': orders.count(),
        'today_sales': sales,
        'pending_payments': PaymentProof.objects.filter(order__status='payment_submitted').count(),
        'customizations': Customization.objects.count(),
        'banners': Banner.objects.count(),
        'stories': StorySlide.objects.count(),
        'conversations': ChatConversation.objects.count(),
        'recent_orders': orders.select_related('user')[:8],
        'recent_users': User.objects.order_by('-date_joined')[:6],
        'recent_chats': ChatConversation.objects.select_related('user').order_by('-updated_at')[:6],
        'links': [
            ('Products','/admin/products/product/'), ('Categories','/admin/categories/category/'),
            ('Orders','/admin/orders/order/'), ('Users','/admin/accounts/user/'),
            ('Customizations','/admin/customization/customization/'),
            ('Payment Proofs','/admin/payments/paymentproof/'),
            ('Banners','/admin/sitecontent/banner/'), ('Stories','/admin/sitecontent/storyslide/'),
            ('Chat Conversations','/admin/chatbot/chatconversation/'), ('Chat Messages','/admin/chatbot/chatmessage/'),
            ('Coupons','/admin/coupons/coupon/'), ('Offers','/admin/offers/offer/'),
            ('Advertisements','/admin/advertisements/advertisement/'), ('Site Settings','/admin/sitecontent/sitesettings/'),
        ],
    }
    return render(request, 'creator_studio/home.html', context)


from django.shortcuts import get_object_or_404

@staff_member_required
def order_detail(request, order_number):
    order = get_object_or_404(
        Order.objects.select_related('user').prefetch_related(
            'items__customization__images', 'payment_proofs'
        ),
        order_number=order_number
    )
    return render(request, 'creator_studio/order_detail.html', {'order': order})

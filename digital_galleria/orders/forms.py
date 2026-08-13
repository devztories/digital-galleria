from django import forms
from .models import Order


class CheckoutForm(forms.Form):
    full_name = forms.CharField(max_length=150)
    email = forms.EmailField()
    phone = forms.CharField(max_length=20)
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}))
    city = forms.CharField(max_length=100)
    district = forms.CharField(max_length=100)
    state = forms.CharField(max_length=100)
    pincode = forms.CharField(max_length=10)
    delivery_notes = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}), required=False)

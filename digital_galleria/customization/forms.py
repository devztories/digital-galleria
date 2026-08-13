from django import forms
from .models import Customization


class CustomizationForm(forms.ModelForm):
    class Meta:
        model = Customization
        fields = ['recipient_name', 'custom_message', 'via_whatsapp']
        widgets = {
            'custom_message': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Add a personal message (optional)'}),
            'recipient_name': forms.TextInput(attrs={'placeholder': "Who is this for?"}),
        }

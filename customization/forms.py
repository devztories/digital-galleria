from django import forms
from .models import ProductCustomization


class ProductCustomizationForm(forms.ModelForm):

    class Meta:

        model = ProductCustomization

        fields = [

            "uploaded_photo",

            "custom_text",

            "font_name",

            "frame_size",

            "frame_color",

            "notes",

        ]

        widgets = {

            "custom_text": forms.TextInput(

                attrs={

                    "class": "form-control",

                    "placeholder": "Enter your custom text"

                }

            ),

            "font_name": forms.Select(

                choices=[

                    ("Poppins", "Poppins"),

                    ("Roboto", "Roboto"),

                    ("Montserrat", "Montserrat"),

                    ("Playfair Display", "Playfair Display"),

                    ("Pacifico", "Pacifico"),

                ],

                attrs={

                    "class": "form-select"

                }

            ),

            "frame_size": forms.Select(

                attrs={

                    "class": "form-select"

                }

            ),

            "frame_color": forms.TextInput(

                attrs={

                    "class": "form-control",

                    "placeholder": "Black, White, Gold..."

                }

            ),

            "notes": forms.Textarea(

                attrs={

                    "class": "form-control",

                    "rows": 4,

                    "placeholder": "Additional Instructions"

                }

            ),

        }
from django import forms
from .models import User, Address, INDIAN_STATE_CHOICES


class RegisterForm(forms.Form):
    name = forms.CharField(max_length=150)
    email = forms.EmailField()
    phone = forms.CharField(max_length=20)
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    def clean_email(self):
        email = self.cleaned_data["email"].lower().strip()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean_phone(self):
        return self.cleaned_data["phone"].strip()

    def clean_password(self):
        pwd = self.cleaned_data["password"]
        if len(pwd) < 4 or len(pwd) > 8:
            raise forms.ValidationError("Password must be between 4 and 8 characters.")
        return pwd

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("password") and cleaned.get("confirm_password"):
            if cleaned["password"] != cleaned["confirm_password"]:
                raise forms.ValidationError("Passwords do not match.")
        return cleaned


class LoginForm(forms.Form):
    email = forms.EmailField()
    phone = forms.CharField(max_length=20)

    def clean(self):
        cleaned = super().clean()
        email = cleaned.get("email")
        phone = cleaned.get("phone")
        if email and phone:
            email = email.lower().strip()
            phone = phone.strip()
            try:
                user = User.objects.get(email=email, phone=phone)
            except User.DoesNotExist:
                raise forms.ValidationError("No account found with that email and phone number.")
            if not user.is_active:
                raise forms.ValidationError("This account is inactive.")
            cleaned["user"] = user
        return cleaned


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["name", "phone", "profile_image"]


class PasswordChangeForm(forms.Form):
    current_password = forms.CharField(widget=forms.PasswordInput)
    new_password = forms.CharField(widget=forms.PasswordInput)
    confirm_new_password = forms.CharField(widget=forms.PasswordInput)

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_current_password(self):
        pwd = self.cleaned_data["current_password"]
        if not self.user.check_password(pwd):
            raise forms.ValidationError("Current password is incorrect.")
        return pwd

    def clean_new_password(self):
        pwd = self.cleaned_data["new_password"]
        if len(pwd) < 4 or len(pwd) > 8:
            raise forms.ValidationError("Password must be between 4 and 8 characters.")
        return pwd

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("new_password") != cleaned.get("confirm_new_password"):
            raise forms.ValidationError("New passwords do not match.")
        return cleaned


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ["full_name", "phone", "house_building", "street", "area",
                  "city", "district", "state", "pincode", "landmark", "is_default"]
        widgets = {
            # A dropdown instead of free text so "Kerala" can never be
            # mistyped (e.g. "Ka", "Karnataka") — the delivery charge and
            # the Kerala/Outside-Kerala split both key off this exact value.
            "state": forms.Select(choices=INDIAN_STATE_CHOICES),
        }

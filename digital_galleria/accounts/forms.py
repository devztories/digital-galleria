from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User


class RegistrationForm(UserCreationForm):
    name = forms.CharField(max_length=150, required=True)
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=20, required=True)
    gender = forms.ChoiceField(choices=User.GENDER_CHOICES, widget=forms.RadioSelect, required=True)

    class Meta:
        model = User
        fields = ['username', 'name', 'email', 'phone', 'gender', 'password1', 'password2']


    def clean_password1(self):
        password = self.cleaned_data.get('password1', '')
        if not 4 <= len(password) <= 16:
            raise forms.ValidationError('Password must be 4–16 characters.')
        if not password.isalnum() or not password.isascii():
            raise forms.ValidationError('Use letters and numbers only.')
        return password

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.name = self.cleaned_data['name']
        user.email = self.cleaned_data['email']
        user.phone = self.cleaned_data['phone']
        user.gender = self.cleaned_data['gender']
        if commit:
            user.save()
        return user


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['name', 'email', 'phone', 'profile_image']


class ThemeForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['theme']

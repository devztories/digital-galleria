from django import forms

from django.contrib.auth.forms import (
    UserCreationForm,
)

from .models import (
    User,
    Address,
)


# =========================================================
# REGISTER FORM
#
# Used only when creating a NEW customer account.
#
# This form:
#
# - Creates user
# - Handles password1/password2
# - Saves email
# - Saves phone
# - Prevents duplicate username
# - Prevents duplicate email
# =========================================================

class RegisterForm(UserCreationForm):

    # =====================================================
    # EMAIL
    # =====================================================

    email = forms.EmailField(

        required=True,

        widget=forms.EmailInput(

            attrs={

                "placeholder":
                    "Enter your email address",

                "autocomplete":
                    "email",

            }

        )

    )


    # =====================================================
    # PHONE
    # =====================================================

    phone = forms.CharField(

        required=False,

        max_length=20,

        widget=forms.TextInput(

            attrs={

                "placeholder":
                    "Enter your phone number",

                "autocomplete":
                    "tel",

            }

        )

    )


    # =====================================================
    # META
    # =====================================================

    class Meta:

        model = User

        fields = [

            "username",

            "email",

            "phone",

            "password1",

            "password2",

        ]


    # =====================================================
    # USERNAME VALIDATION
    # =====================================================

    def clean_username(self):

        username = self.cleaned_data.get(
            "username"
        )


        if not username:

            return username


        username = username.strip()


        if (

            User.objects

            .filter(
                username__iexact=username
            )

            .exists()

        ):

            raise forms.ValidationError(

                "This username is already taken."

            )


        return username


    # =====================================================
    # EMAIL VALIDATION
    # =====================================================

    def clean_email(self):

        email = self.cleaned_data.get(
            "email"
        )


        if not email:

            return email


        email = (

            email

            .strip()

            .lower()

        )


        if (

            User.objects

            .filter(
                email__iexact=email
            )

            .exists()

        ):

            raise forms.ValidationError(

                (
                    "An account with this email "
                    "already exists."
                )

            )


        return email


    # =====================================================
    # PHONE CLEANING
    # =====================================================

    def clean_phone(self):

        phone = self.cleaned_data.get(
            "phone"
        )


        if phone:

            phone = phone.strip()


        return phone


    # =====================================================
    # SAVE USER
    # =====================================================

    def save(
        self,
        commit=True
    ):

        user = super().save(
            commit=False
        )


        user.email = (

            self.cleaned_data.get(
                "email",
                ""
            )

        )


        user.phone = (

            self.cleaned_data.get(
                "phone",
                ""
            )

        )


        if commit:

            user.save()


        return user


# =========================================================
# PROFILE FORM
#
# Used only for editing CURRENT logged-in user.
#
# Updates:
#
# - Username
# - First name
# - Last name
# - Email
# - Phone
# - Profile image
#
# Does NOT:
#
# - Create account
# - Change password
# =========================================================

class ProfileForm(forms.ModelForm):

    # =====================================================
    # META
    # =====================================================

    class Meta:

        model = User

        fields = [

            "username",

            "first_name",

            "last_name",

            "email",

            "phone",

            "profile_image",

        ]


        widgets = {

            "username":

                forms.TextInput(

                    attrs={

                        "placeholder":
                            "Enter your username",

                        "autocomplete":
                            "username",

                    }

                ),


            "first_name":

                forms.TextInput(

                    attrs={

                        "placeholder":
                            "Enter your first name",

                        "autocomplete":
                            "given-name",

                    }

                ),


            "last_name":

                forms.TextInput(

                    attrs={

                        "placeholder":
                            "Enter your last name",

                        "autocomplete":
                            "family-name",

                    }

                ),


            "email":

                forms.EmailInput(

                    attrs={

                        "placeholder":
                            "Enter your email address",

                        "autocomplete":
                            "email",

                    }

                ),


            "phone":

                forms.TextInput(

                    attrs={

                        "placeholder":
                            "Enter your phone number",

                        "autocomplete":
                            "tel",

                    }

                ),

        }


    # =====================================================
    # USERNAME VALIDATION
    # =====================================================

    def clean_username(self):

        username = self.cleaned_data.get(
            "username"
        )


        if not username:

            return username


        username = username.strip()


        existing_user = (

            User.objects

            .exclude(
                pk=self.instance.pk
            )

            .filter(
                username__iexact=username
            )

            .exists()

        )


        if existing_user:

            raise forms.ValidationError(

                "This username is already taken."

            )


        return username


    # =====================================================
    # EMAIL VALIDATION
    # =====================================================

    def clean_email(self):

        email = self.cleaned_data.get(
            "email"
        )


        if not email:

            return email


        email = (

            email

            .strip()

            .lower()

        )


        existing_user = (

            User.objects

            .exclude(
                pk=self.instance.pk
            )

            .filter(
                email__iexact=email
            )

            .exists()

        )


        if existing_user:

            raise forms.ValidationError(

                (
                    "This email address "
                    "is already in use."
                )

            )


        return email


    # =====================================================
    # PHONE CLEANING
    # =====================================================

    def clean_phone(self):

        phone = self.cleaned_data.get(
            "phone"
        )


        if phone:

            phone = phone.strip()


        return phone


# =========================================================
# ADDRESS FORM
#
# Used for:
#
# - Add new saved address
# - Edit saved address
# - Set address as default
#
# Address belongs to request.user.
# User is NOT selectable from this form.
# =========================================================

class AddressForm(forms.ModelForm):

    # =====================================================
    # META
    # =====================================================

    class Meta:

        model = Address


        fields = [

            "address_type",

            "full_name",

            "phone",

            "address_line1",

            "address_line2",

            "city",

            "state",

            "pincode",

            "is_default",

        ]


        # =================================================
        # WIDGETS
        # =================================================

        widgets = {

            # ---------------------------------------------
            # ADDRESS TYPE
            # ---------------------------------------------

            "address_type":

                forms.Select(

                    attrs={

                        "class":
                            "form-select",

                    }

                ),


            # ---------------------------------------------
            # FULL NAME
            # ---------------------------------------------

            "full_name":

                forms.TextInput(

                    attrs={

                        "class":
                            "form-control",

                        "placeholder":
                            "Receiver full name",

                        "autocomplete":
                            "name",

                    }

                ),


            # ---------------------------------------------
            # PHONE
            # ---------------------------------------------

            "phone":

                forms.TextInput(

                    attrs={

                        "class":
                            "form-control",

                        "placeholder":
                            "10-digit mobile number",

                        "autocomplete":
                            "tel",

                        "inputmode":
                            "tel",

                    }

                ),


            # ---------------------------------------------
            # ADDRESS LINE 1
            # ---------------------------------------------

            "address_line1":

                forms.TextInput(

                    attrs={

                        "class":
                            "form-control",

                        "placeholder":
                            (
                                "House / Flat / Building / "
                                "Street"
                            ),

                        "autocomplete":
                            "address-line1",

                    }

                ),


            # ---------------------------------------------
            # ADDRESS LINE 2
            # ---------------------------------------------

            "address_line2":

                forms.TextInput(

                    attrs={

                        "class":
                            "form-control",

                        "placeholder":
                            (
                                "Area / Locality / Landmark "
                                "(Optional)"
                            ),

                        "autocomplete":
                            "address-line2",

                    }

                ),


            # ---------------------------------------------
            # CITY
            # ---------------------------------------------

            "city":

                forms.TextInput(

                    attrs={

                        "class":
                            "form-control",

                        "placeholder":
                            "City / Town",

                        "autocomplete":
                            "address-level2",

                    }

                ),


            # ---------------------------------------------
            # STATE
            # ---------------------------------------------

            "state":

                forms.TextInput(

                    attrs={

                        "class":
                            "form-control",

                        "placeholder":
                            "State",

                        "autocomplete":
                            "address-level1",

                    }

                ),


            # ---------------------------------------------
            # PINCODE
            # ---------------------------------------------

            "pincode":

                forms.TextInput(

                    attrs={

                        "class":
                            "form-control",

                        "placeholder":
                            "6-digit pincode",

                        "autocomplete":
                            "postal-code",

                        "inputmode":
                            "numeric",

                        "maxlength":
                            "6",

                    }

                ),


            # ---------------------------------------------
            # DEFAULT CHECKBOX
            # ---------------------------------------------

            "is_default":

                forms.CheckboxInput(

                    attrs={

                        "class":
                            "form-check-input",

                    }

                ),

        }


    # =====================================================
    # CLEAN FULL NAME
    # =====================================================

    def clean_full_name(self):

        full_name = self.cleaned_data.get(
            "full_name",
            ""
        )


        full_name = full_name.strip()


        if len(full_name) < 2:

            raise forms.ValidationError(

                "Please enter a valid full name."

            )


        return full_name


    # =====================================================
    # CLEAN PHONE
    #
    # Accept:
    #
    # 9876543210
    # +91 9876543210
    # 98765-43210
    #
    # Saves cleaned numeric format while preserving
    # optional leading +.
    # =====================================================

    def clean_phone(self):

        phone = self.cleaned_data.get(
            "phone",
            ""
        )


        phone = phone.strip()


        # Remove common separators.

        cleaned_phone = (

            phone

            .replace(
                " ",
                ""
            )

            .replace(
                "-",
                ""
            )

            .replace(
                "(",
                ""
            )

            .replace(
                ")",
                ""
            )

        )


        # Allow optional + at beginning.

        digits = cleaned_phone


        if digits.startswith("+"):

            digits = digits[1:]


        if not digits.isdigit():

            raise forms.ValidationError(

                "Enter a valid phone number."

            )


        if len(digits) < 10:

            raise forms.ValidationError(

                (
                    "Phone number must contain "
                    "at least 10 digits."
                )

            )


        if len(digits) > 15:

            raise forms.ValidationError(

                "Phone number is too long."

            )


        return cleaned_phone


    # =====================================================
    # CLEAN ADDRESS LINE 1
    # =====================================================

    def clean_address_line1(self):

        address = self.cleaned_data.get(

            "address_line1",

            ""

        )


        address = address.strip()


        if len(address) < 3:

            raise forms.ValidationError(

                (
                    "Please enter a complete "
                    "delivery address."
                )

            )


        return address


    # =====================================================
    # CLEAN ADDRESS LINE 2
    # =====================================================

    def clean_address_line2(self):

        address = self.cleaned_data.get(

            "address_line2",

            ""

        )


        return address.strip()


    # =====================================================
    # CLEAN CITY
    # =====================================================

    def clean_city(self):

        city = self.cleaned_data.get(
            "city",
            ""
        )


        city = city.strip()


        if not city:

            raise forms.ValidationError(

                "Please enter your city."

            )


        return city


    # =====================================================
    # CLEAN STATE
    # =====================================================

    def clean_state(self):

        state = self.cleaned_data.get(
            "state",
            ""
        )


        state = state.strip()


        if not state:

            raise forms.ValidationError(

                "Please enter your state."

            )


        return state


    # =====================================================
    # CLEAN PINCODE
    #
    # Digital Galleria currently targets Indian
    # delivery addresses, so require exactly 6 digits.
    # =====================================================

    def clean_pincode(self):

        pincode = self.cleaned_data.get(

            "pincode",

            ""

        )


        pincode = pincode.strip()


        if not pincode.isdigit():

            raise forms.ValidationError(

                "Pincode must contain only numbers."

            )


        if len(pincode) != 6:

            raise forms.ValidationError(

                "Enter a valid 6-digit pincode."

            )


        return pincode
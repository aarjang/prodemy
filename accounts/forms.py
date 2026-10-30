from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

User = get_user_model()


class SignUpForm(UserCreationForm):
    """Sign-up with email and password. Emails are unique, compared case-insensitively."""

    class Meta:
        model = User
        fields = ("email",)
        labels = {"email": "ایمیل"}

    error_messages = {"password_mismatch": "دو رمز عبور یکسان نیستند."}

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("با این ایمیل قبلاً حساب ساخته شده است.")
        return email


class EmailAuthenticationForm(AuthenticationForm):
    """The built-in login form with a Persian email label and one generic error."""

    error_messages = {
        "invalid_login": "ایمیل یا رمز عبور درست نیست.",
        "inactive": "این حساب غیرفعال شده است.",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "ایمیل"
        self.fields["username"].widget.attrs["autocomplete"] = "email"
        self.fields["password"].label = "رمز عبور"

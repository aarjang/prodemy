from django import forms

from alerts.models import PriceAlert
from core.numbers import parse_toman


class AlertForm(forms.ModelForm):
    """Create/edit a price alert. The threshold accepts Persian, Arabic-Indic and Western digits."""

    threshold = forms.CharField(
        label="قیمت آستانه (تومان)",
        help_text="مثلاً ۲۷۱٬۰۰۰ — عدد صحیح به تومان.",
    )

    class Meta:
        model = PriceAlert
        fields = ("threshold", "direction", "signal", "note")
        labels = {"direction": "جهت", "signal": "سیگنال", "note": "یادداشت (اختیاری)"}
        help_texts = {
            "signal": "هر جهتی را می‌توانید با خرید یا فروش ترکیب کنید؛ مثلاً «بالاتر از X → خرید».",
        }
        widgets = {
            "direction": forms.RadioSelect,
            "signal": forms.RadioSelect,
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user or getattr(self.instance, "user", None)
        # Radio groups must not render the "---------" empty choice.
        self.fields["direction"].choices = PriceAlert.Direction.choices
        self.fields["signal"].choices = PriceAlert.Signal.choices
        if self.instance.pk:
            # model_to_dict seeds a Decimal here; the field is a CharField, so a Decimal
            # initial would make has_changed() report every submit as a threshold change.
            self.initial["threshold"] = str(int(self.instance.threshold))

    def clean_threshold(self):
        try:
            value = parse_toman(self.cleaned_data["threshold"])
        except ValueError:
            raise forms.ValidationError("قیمت باید یک عدد صحیح به تومان باشد؛ مثلاً ۲۷۱٬۰۰۰.")
        if value <= 0:
            raise forms.ValidationError("قیمت باید بزرگ‌تر از صفر باشد.")
        return value

    def clean(self):
        cleaned = super().clean()
        creating = self.instance.pk is None
        if creating and self.user is not None:
            active = self.user.alerts.filter(state__in=PriceAlert.ACTIVE_STATES).count()
            if active >= PriceAlert.MAX_ACTIVE_PER_USER:
                raise forms.ValidationError(
                    "بیشتر از ۲۰ هشدار فعال نمی‌توانید داشته باشید. یکی را متوقف یا حذف کنید."
                )
        return cleaned

    def save(self, commit=True):
        alert = super().save(commit=False)
        if self.user is not None:
            alert.user = self.user
        rearming_change = {"threshold", "direction"} & set(self.changed_data)
        if self.instance.pk and rearming_change and alert.state != PriceAlert.State.PAUSED:
            alert.state = PriceAlert.State.ARMED
        if commit:
            alert.save()
        return alert

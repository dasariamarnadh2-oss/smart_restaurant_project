from django import forms
from .models import Order


class CheckoutForm(forms.Form):
    customer_name = forms.CharField(max_length=120, label="Your name", widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter your name"}))
    table_number = forms.IntegerField(min_value=1, max_value=999, label="Table number", widget=forms.NumberInput(attrs={"class": "form-control", "min": "1"}))

    def clean_customer_name(self):
        name = self.cleaned_data["customer_name"].strip()
        if not name:
            raise forms.ValidationError("Please enter your name.")
        return name


class OrderStatusForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["status"]
        widgets = {"status": forms.Select(attrs={"class": "form-select"})}

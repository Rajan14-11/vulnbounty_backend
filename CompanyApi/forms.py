from django import forms
from .models import Transaction

class CompanyPaymentForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ('amount', 'description',)
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
        }
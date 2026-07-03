from django import forms
from .models import Reservation

class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ['room', 'guest', 'number_of_guests', 'check_in', 'check_out']
        # adding calendar attributes
        widgets = {
            'room': forms.Select(attrs={'class': 'form-select'}),
            'guest': forms.Select(attrs={'class': 'form-select'}),
            'number_of_guests': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'check_in': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'check_out': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }
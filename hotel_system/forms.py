from django import forms
from .models import Reservation, RoomServiceOrder

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


class RoomServiceOrderForm(forms.ModelForm):
    class Meta:
        model = RoomServiceOrder
        fields = ['reservation', 'item', 'quantity']
        widgets = {
            'reservation': forms.Select(attrs={'class': 'form-select'}),
            'item': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
        }
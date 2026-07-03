from django.shortcuts import render, redirect
from django.contrib import messages 
from .models import Room
from .forms import ReservationForm

def home(request):
    rooms = Room.objects.all()
    if request.method == 'POST':
        form = ReservationForm(request.POST)
        if form.is_valid():
            # save the reservation and calculate the total price
            reservation = form.save() 
            messages.success(
                request, 
                f"Успешна резервация! Вашата крайна сметка за престоя е: {reservation.total_price} лв."
            )
            return redirect('home')
        else:
            # shaw error messages
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = ReservationForm()

    return render(request, 'hotel_system/home.html', {
        'rooms': rooms,
        'form': form
    })
from django.shortcuts import render, redirect
from .models import Room
from .forms import ReservationForm

def home(request):
    rooms = Room.objects.all()
    
    # Handle form submission
    if request.method == 'POST':
        form = ReservationForm(request.POST)
        if form.is_valid():
            form.save() # save the reservation to the database
            return redirect('home') # reload the page to show the updated list of rooms
    else:
        # Show an empty form for requests
        form = ReservationForm()

    return render(request, 'hotel_system/home.html', {
        'rooms': rooms,
        'form': form
    })
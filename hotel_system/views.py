from django.shortcuts import render
from .models import Room

def home(request):
    rooms = Room.objects.all() # all rooms from the database
    return render(request, 'hotel_system/home.html', {'rooms': rooms}) # home.html template with rooms context

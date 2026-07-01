from django.contrib import admin
from .models import Room, Guest, Reservation

# Register your models here.
admin.site.register(Room)
admin.site.register(Guest)
admin.site.register(Reservation)
from django.contrib import admin
from .models import Room, Guest, Reservation, Housekeeping, RoomServiceOrder

admin.site.register(Room)
admin.site.register(Guest)
admin.site.register(Reservation)
admin.site.register(Housekeeping)
admin.site.register(RoomServiceOrder)
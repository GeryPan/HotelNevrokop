from django.shortcuts import render, redirect
from django.contrib import messages 
from .models import Room
from .forms import ReservationForm, RoomServiceOrderForm

def home(request):
    rooms = Room.objects.all()
    if request.method == 'POST':
        # submit_reservation and submit_order are the names of the submit buttons in the HTML form
        if 'submit_reservation' in request.POST:
            reservation_form = ReservationForm(request.POST)
            order_form = RoomServiceOrderForm()
            if reservation_form.is_valid():
                reservation = reservation_form.save()
                messages.success(request, f"Успешна резервация за стая {reservation.room.number}! Обща цена: {reservation.total_price} лв.")
                return redirect('home')
            else:
                messages.error(request, "Грешка при резервацията. Моля, проверете въведените данни.")
                
        elif 'submit_order' in request.POST:
            order_form = RoomServiceOrderForm(request.POST)
            reservation_form = ReservationForm()
            if order_form.is_valid():
                order = order_form.save()
                messages.success(request, f"Поръчката за {order.item.name} (x{order.quantity}) беше изпратена към стая {order.reservation.room.number}!")
                return redirect('home')
            else:
                messages.error(request, "Грешка при поръчката. Количеството трябва да бъде поне 1.")
    else:
        reservation_form = ReservationForm()
        order_form = RoomServiceOrderForm()

    return render(request, 'hotel_system/home.html', {
        'rooms': rooms,
        'form': reservation_form,
        'order_form': order_form,
    })
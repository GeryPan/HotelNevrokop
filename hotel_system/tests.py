from django.test import TestCase
from django.core.exceptions import ValidationError
from datetime import date, timedelta
from .models import Room, Guest, Reservation

class ReservationModelTest(TestCase):
    def setUp(self):
        # shit data for the tests
        self.room = Room.objects.create(
            number="101",
            room_type="single",
            capacity=1,
            price_per_night=50.00
        )
        self.guest = Guest.objects.create(
            name="Иван Иванов",
            phone="0888123456",
            email="ivan@example.com"
        )

    def test_past_check_in_date_raises_error(self):
        past_date = date.today() - timedelta(days=5)
        future_date = date.today() + timedelta(days=5)
        
        reservation = Reservation(
            room=self.room,
            guest=self.guest,
            number_of_guests=1,
            check_in=past_date,
            check_out=future_date
        )
        
        # Verify that the ValidationError is correctly raised
        with self.assertRaises(ValidationError):
            reservation.clean()

from django.test import TestCase
from django.core.exceptions import ValidationError
from datetime import date, timedelta
from .models import Room, Guest, Reservation

class ReservationModelTest(TestCase):
    def setUp(self):
        # схит data for the tests
        self.room = Room.objects.create(
            number="101",
            room_type="single",
            capacity=2, 
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
            room=self.room, guest=self.guest, number_of_guests=1,
            check_in=past_date, check_out=future_date
        )
        with self.assertRaises(ValidationError):
            reservation.clean()

    def test_checkout_before_checkin_raises_error(self):
        # checkout before check-in
        check_in_date = date.today() + timedelta(days=5)
        check_out_date = date.today() + timedelta(days=2)
        reservation = Reservation(
            room=self.room, guest=self.guest, number_of_guests=1,
            check_in=check_in_date, check_out=check_out_date
        )
        with self.assertRaises(ValidationError):
            reservation.clean()

    def test_exceeding_room_capacity_raises_error(self):
        # 3 guests for a room with capacity of 2
        check_in_date = date.today() + timedelta(days=2)
        check_out_date = date.today() + timedelta(days=5)
        reservation = Reservation(
            room=self.room, guest=self.guest, number_of_guests=3,
            check_in=check_in_date, check_out=check_out_date
        )
        with self.assertRaises(ValidationError):
            reservation.clean()

    def test_total_price_calculation(self):
        # 3 nights stay (3 * 50 = 150.00)
        check_in_date = date.today() + timedelta(days=1)
        check_out_date = date.today() + timedelta(days=4)
        reservation = Reservation(
            room=self.room, guest=self.guest, number_of_guests=1,
            check_in=check_in_date, check_out=check_out_date
        )
        self.assertEqual(reservation.total_price, 150.00)

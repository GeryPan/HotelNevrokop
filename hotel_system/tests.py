from django.test import TestCase
from django.core.exceptions import ValidationError
from datetime import date, timedelta
from .models import Room, Guest, Reservation, Housekeeping

class HotelSystemTests(TestCase):
    def setUp(self):
        self.room = Room.objects.create(
            number="101", room_type="single", capacity=2, price_per_night=50.00
        )
        self.guest = Guest.objects.create(
            name="Иван Иванов", phone="0888123456", email="ivan@example.com"
        )

    # reservation tests
    def test_1_valid_reservation_creation(self):
        reservation = Reservation.objects.create(
            room=self.room, guest=self.guest, number_of_guests=1,
            check_in=date.today() + timedelta(days=1),
            check_out=date.today() + timedelta(days=3)
        )
        self.assertEqual(Reservation.objects.count(), 1)

    def test_2_past_check_in_date_raises_error(self):
        reservation = Reservation(
            room=self.room, guest=self.guest, number_of_guests=1,
            check_in=date.today() - timedelta(days=2),
            check_out=date.today() + timedelta(days=2)
        )
        with self.assertRaises(ValidationError):
            reservation.clean()

    def test_3_checkout_before_checkin_raises_error(self):
        reservation = Reservation(
            room=self.room, guest=self.guest, number_of_guests=1,
            check_in=date.today() + timedelta(days=3),
            check_out=date.today() + timedelta(days=1)
        )
        with self.assertRaises(ValidationError):
            reservation.clean()

    def test_4_zero_guests_raises_error(self):
        reservation = Reservation(
            room=self.room, guest=self.guest, number_of_guests=0,
            check_in=date.today() + timedelta(days=1),
            check_out=date.today() + timedelta(days=3)
        )
        with self.assertRaises(ValidationError):
            reservation.clean()

    def test_5_exceeding_room_capacity_raises_error(self):
        reservation = Reservation(
            room=self.room, guest=self.guest, number_of_guests=3,
            check_in=date.today() + timedelta(days=1),
            check_out=date.today() + timedelta(days=3)
        )
        with self.assertRaises(ValidationError):
            reservation.clean()

    def test_6_overlapping_reservations_raises_error(self):
        Reservation.objects.create(
            room=self.room, guest=self.guest, number_of_guests=1,
            check_in=date.today() + timedelta(days=1),
            check_out=date.today() + timedelta(days=5)
        )
        overlapping_reservation = Reservation(
            room=self.room, guest=self.guest, number_of_guests=1,
            check_in=date.today() + timedelta(days=3),
            check_out=date.today() + timedelta(days=7)
        )
        with self.assertRaises(ValidationError):
            overlapping_reservation.clean()

    def test_7_total_price_calculation(self):
        reservation = Reservation(
            room=self.room, guest=self.guest, number_of_guests=1,
            check_in=date.today() + timedelta(days=1),
            check_out=date.today() + timedelta(days=4)
        )
        self.assertEqual(reservation.total_price, 150.00)

    # guest tests
    def test_8_guest_invalid_phone_raises_error(self):
        invalid_guest = Guest(name="Петър", phone="invalid_phone", email="petar@test.com")
        with self.assertRaises(ValidationError):
            invalid_guest.full_clean()

    def test_9_guest_valid_phone_passes(self):
        valid_guest = Guest(name="Мария", phone="+359888112233", email="maria@test.com")
        valid_guest.full_clean() # Не трябва да хвърля грешка
        self.assertEqual(valid_guest.name, "Мария")

    # housekeeping tests
    def test_10_housekeeping_valid_creation(self):
        cleaning = Housekeeping.objects.create(
            room=self.room, date=date.today(), is_cleaned=True
        )
        self.assertTrue(cleaning.is_cleaned)

    def test_11_housekeeping_future_date_raises_error(self):
        cleaning = Housekeeping(
            room=self.room, date=date.today() + timedelta(days=1), is_cleaned=True
        )
        with self.assertRaises(ValidationError):
            cleaning.clean()
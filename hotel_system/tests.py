from django.test import TestCase
from django.core.exceptions import ValidationError
from datetime import date, timedelta
from .models import Room, Guest, Reservation, Housekeeping, RoomServiceItem, RoomServiceOrder
from django.core.exceptions import ValidationError

class HotelSystemTests(TestCase):
    def setUp(self):
        self.room = Room.objects.create(
            number="101", room_type="single", capacity=2, price_per_night=50.00
        )
        self.guest = Guest.objects.create(
            name="Иван Иванов", phone="0888123456", email="ivan@example.com"
        )
        self.whiskey, _ = RoomServiceItem.objects.get_or_create(
            name="Шотландско уиски (50ml)", defaults={'price': 8.00}
        )
        self.chips, _ = RoomServiceItem.objects.get_or_create(
            name="Чипс Голям", defaults={'price': 3.50}
        )
        self.cola, _ = RoomServiceItem.objects.get_or_create(
            name="Кока-Кола", defaults={'price': 3.00}
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

    # room service tests
    def test_12_room_service_order_calculation(self):
        res = Reservation.objects.create(
            room=self.room, guest=self.guest, number_of_guests=1,
            check_in=date.today(), check_out=date.today() + timedelta(days=2)
        )
        order = RoomServiceOrder.objects.create(
            reservation=res, item=self.whiskey, quantity=3
        )
        self.assertEqual(order.order_total, 24.00)

    # check if room.active_room_service_total is calculated correctly
    def test_13_room_active_service_total(self): 
        res = Reservation.objects.create(
            room=self.room, guest=self.guest, number_of_guests=1,
            check_in=date.today(), check_out=date.today() + timedelta(days=2)
        )
        RoomServiceOrder.objects.create(reservation=res, item=self.chips, quantity=1)
        RoomServiceOrder.objects.create(reservation=res, item=self.cola, quantity=1)
        
        self.assertEqual(self.room.active_room_service_total, 6.50)

    def test_14_zero_quantity_raises_error(self):
        res = Reservation.objects.create(
            room=self.room, guest=self.guest, number_of_guests=1,
            check_in=date.today(), check_out=date.today() + timedelta(days=2)
        )
        # Опит за поръчка с невалидно количество (0)
        bad_order = RoomServiceOrder(
            reservation=res, item=self.cola, quantity=0
        )
        # Трябва да хвърли ValidationError при извикване на clean()
        with self.assertRaises(ValidationError):
            bad_order.clean()

    # test if new menu item can be created
    def test_15_menu_item_creation(self):
        initial_count = RoomServiceItem.objects.count()
        new_item = RoomServiceItem.objects.create(name="Енергийна напитка", price=5.50)
        self.assertEqual(RoomServiceItem.objects.count(), initial_count + 1)
        self.assertEqual(new_item.price, 5.50)

    # negative price for room should raise ValidationError
    def test_16_room_negative_price_raises_error(self):
        bad_room = Room(number="102", room_type="double", capacity=2, price_per_night=-20.00)
        with self.assertRaises(ValidationError):
            bad_room.full_clean() # Очакваме Django да хване отрицателната цена

    # invalid email for guest should raise ValidationError
    def test_17_guest_invalid_email_raises_error(self):
        bad_guest = Guest(name="Петър", phone="0888999777", email="petar-invalid-email.com")
        with self.assertRaises(ValidationError):
            bad_guest.full_clean() # Очакваме грешка, защото няма '@' и правилен домейн

    # check-out -> check-in in the same day reservations should be allowed
    def test_18_back_to_back_reservations_allowed(self):
        Reservation.objects.create(
            room=self.room, guest=self.guest, number_of_guests=1,
            check_in=date.today() + timedelta(days=1),
            check_out=date.today() + timedelta(days=3)
        )
        new_res = Reservation(
            room=self.room, guest=self.guest, number_of_guests=1,
            check_in=date.today() + timedelta(days=3),
            check_out=date.today() + timedelta(days=5)
        )
        try:
            new_res.clean()
        except ValidationError:
            self.fail("Резервация 'гръб в гръб' хвърли неочаквана ValidationError. Проблем с логиката за напускане-настаняване!")

    # changing housekeeping status from False to True should be reflected in the database
    def test_19_housekeeping_status_update(self):
        cleaning = Housekeeping.objects.create(
            room=self.room, date=date.today(), is_cleaned=False
        )
        self.assertFalse(cleaning.is_cleaned)
        cleaning.is_cleaned = True
        cleaning.save()
        self.assertTrue(Housekeeping.objects.get(id=cleaning.id).is_cleaned)

    # negaative price for product should raise ValidationError
    def test_20_item_negative_price_raises_error(self):
        bad_item = RoomServiceItem(name="Безплатен обяд", price=-5.00)
        with self.assertRaises(ValidationError):
            bad_item.full_clean()
            